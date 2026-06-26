from dotenv import load_dotenv
load_dotenv()

import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
from db import init_db, close_pool, create_analysis, update_analysis, get_history, get_pool
from auth import hash_password, verify_password, create_token, decode_token

_ws_connections: dict[str, WebSocket] = {}
_bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception:
        pass
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


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return decode_token(credentials.credentials)


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict | None:
    if not credentials:
        return None
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

class AuthRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup")
async def signup(body: AuthRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", body.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered.")
        password_hash = hash_password(body.password)
        row = await conn.fetchrow(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email",
            body.email,
            password_hash,
        )
    token = create_token(str(row["id"]), row["email"])
    return {"access_token": token, "token_type": "bearer", "email": row["email"]}


@app.post("/api/auth/login")
async def login(body: AuthRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash FROM users WHERE email = $1", body.email
        )
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_token(str(row["id"]), row["email"])
    return {"access_token": token, "token_type": "bearer", "email": row["email"]}


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/progress/{analysis_id}")
async def websocket_progress(websocket: WebSocket, analysis_id: str):
    await websocket.accept()
    _ws_connections[analysis_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.pop(analysis_id, None)


async def _push(analysis_id: str, message: str) -> None:
    ws = _ws_connections.get(analysis_id)
    if ws:
        try:
            await ws.send_json({"status": "progress", "message": message})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

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


class AnalyzeRequest(BaseModel):
    region: str


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest, user: dict = Depends(get_current_user)):
    analysis_id = str(uuid.uuid4())

    try:
        db_id = await create_analysis(user["sub"], request.region)
        analysis_id = db_id
    except Exception:
        pass

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

    await _push(analysis_id, f"Scanning active services in {request.region}...")

    await _push(analysis_id, "Analyzing costs with AI...")
    try:
        analysis = await asyncio.to_thread(ai_analyze, scan_result)
    except AIAnalyzerConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIAnalyzerError as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        pass

    await _push(analysis_id, "Analysis complete")
    return {"analysis_id": analysis_id, **analysis}


@app.get("/api/history")
async def history(
    limit: int = Query(default=20, le=100),
    user: dict = Depends(get_current_user),
):
    try:
        records = await get_history(user["sub"], limit)
        return {"analyses": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
