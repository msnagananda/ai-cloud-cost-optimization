from dotenv import load_dotenv
load_dotenv()

import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aws_scanner import (
    AWSCLINotFoundError,
    AWSCredentialsError,
    AWSPermissionError,
    AWSError,
    get_enabled_regions,
    scan_active_resources,
)
from ai_analyzer import (
    AIAnalyzerConnectionError,
    AIAnalyzerError,
    analyze as ai_analyze,
)
from db import init_db, close_pool, create_analysis, update_analysis, get_history


# Tracks active WebSocket connections keyed by analysis_id
_ws_connections: dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception:
        pass  # DB optional — app still starts without it
    yield
    await close_pool()


app = FastAPI(title="AI Cloud Cost Detective", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    region: str
    user_id: str | None = None


async def _push(analysis_id: str, message: str) -> None:
    ws = _ws_connections.get(analysis_id)
    if ws:
        try:
            await ws.send_json({"status": "progress", "message": message})
        except Exception:
            pass


@app.websocket("/ws/progress/{analysis_id}")
async def websocket_progress(websocket: WebSocket, analysis_id: str):
    await websocket.accept()
    _ws_connections[analysis_id] = websocket
    try:
        # Hold the connection open until the client disconnects
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.pop(analysis_id, None)


@app.get("/api/regions")
def list_regions():
    try:
        regions = get_enabled_regions()
        return {"regions": regions}
    except AWSCLINotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AWSError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    analysis_id = str(uuid.uuid4())

    # Persist initial record if DB is available
    try:
        db_id = await create_analysis(request.user_id, request.region)
        analysis_id = db_id
    except Exception:
        pass  # proceed without DB

    # Step ③④ — Cost Explorer + dynamic resource scan
    await _push(analysis_id, "Querying AWS Cost Explorer for active services...")
    try:
        scan_result = await asyncio.to_thread(scan_active_resources, request.region)
    except AWSCLINotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AWSError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Step ⑤ — targeted resource queries complete (inside scan_active_resources)
    await _push(analysis_id, f"Scanning active services in {request.region}...")

    # Step ⑦ — AI analysis
    await _push(analysis_id, "Analyzing costs with AI...")
    try:
        analysis = await asyncio.to_thread(ai_analyze, scan_result)
    except AIAnalyzerConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIAnalyzerError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Step ⑧ — persist result
    await _push(analysis_id, "Storing results...")
    try:
        savings = str(analysis.get("total_estimated_monthly_savings_usd", 0))
        await update_analysis(
            analysis_id,
            status="completed",
            resources_scanned=analysis.get("total_resources_scanned", 0),
            issues_found=len(analysis.get("issues", [])),
            estimated_savings=savings,
            analysis_result=analysis,
        )
    except Exception:
        pass  # non-fatal if DB unavailable

    await _push(analysis_id, "Analysis complete")

    return {"analysis_id": analysis_id, **analysis}


@app.get("/api/history")
async def history(user_id: str | None = Query(default=None), limit: int = Query(default=20, le=100)):
    try:
        records = await get_history(user_id, limit)
        return {"analyses": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
