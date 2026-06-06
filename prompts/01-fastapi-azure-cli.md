# Prompt 1: FastAPI Backend + AWS CLI

Create a Python FastAPI backend in a `backend/` folder for the AI Cloud Cost Detective project.

## What to build

- A FastAPI server with a `POST /api/analyze` endpoint that accepts `{ "region": "<region_name>" }`.
- A `GET /api/regions` endpoint that returns a list of enabled AWS regions.
- Use Python's `subprocess` module to run AWS CLI commands using a cost-driven dynamic discovery approach::
  - `aws ce get-cost-and-usage` to determine which services are currently active (incurring charges) in the account for the current billing cycle.
  - Run specific resource queries only for the active services identified by Cost Explorer (e.g.`aws ec2 describe-instances, aws rds describe-db-instances, aws s3api list-buckets`, etc.).
- Parse the AWS CLI JSON outputs and return an aggregated, structured payload containing the resource type, identifier/name, configuration specifications, and tag metadata (handling untagged resources seamlessly).
- Add error handling for AWS CLI not installed, credentials not configured (`aws configure`), or insufficient IAM permissions (`ce:GetCostAndUsage` and service read permissions).
- Enable CORS for `http://localhost:5173`.
- Include a `requirements.txt` with `fastapi`, `uvicorn`.

## Project structure

```
backend/
├── main.py
├── azure_scanner.py
├── requirements.txt
```

Refer to `Architecture.MD` and `RequestFlow.MD`. This covers steps ③, ④, and ⑤ of the updated request flow.
