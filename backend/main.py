from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
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
    AIAnalyzerAuthError,
    AIAnalyzerConnectionError,
    AIAnalyzerError,
    analyze as ai_analyze,
)

app = FastAPI(title="AI Cloud Cost Detective")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    region: str


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
def analyze(request: AnalyzeRequest):
    # Step ③④⑤ — scan AWS resources via CLI
    try:
        scan_result = scan_active_resources(request.region)
    except AWSCLINotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AWSError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Step ⑦ — run AI analysis on the scan payload
    try:
        analysis = ai_analyze(scan_result)
    except AIAnalyzerAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AIAnalyzerConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIAnalyzerError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return analysis
