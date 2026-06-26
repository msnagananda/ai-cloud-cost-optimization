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
    try:
        result = scan_active_resources(request.region)
        return result
    except AWSCLINotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AWSError as e:
        raise HTTPException(status_code=500, detail=str(e))
