# AI Cloud Cost Detective

An AI-powered tool that investigates AWS cloud costs automatically. It scans resources in an AWS Account / Region, detects cost issues like over-provisioning and misconfigurations, and provides actionable suggestions with fixes.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite + TypeScript + Tailwind) |
| Backend | Python (FastAPI) |
| Auth | Custom JWT Auth (bcrypt + PyJWT) |
| Cloud Data | Aws CLI |
| Cloud | Aws |
| AI Analysis | OpenAI API |
| Database | AWS RDS for PostgreSQL |
| Live Updates | FastAPI WebSocket |

## Architecture

```
                              ┌──────────────┐
                              │     USER     │
                              └──────┬───────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │  REACT FRONTEND   │
                           └────────┬──────────┘
                                    :
                                    : Login / Signup
                                    ▼
                           ┌───────────────────┐
                           │  PYTHON BACKEND   │
                           │    (FastAPI)      │
                           │                   │
                           │  · Custom JWT Auth│
                           └───┬───────┬───┬───┘
                               :       :   :
                ┌──────────────┘       :   └──────────────┐
                :                      :                  :
                ▼                      ▼                  ▼
         ┌─────────────--┐     ┌──────────────┐    ┌──────────────┐
         │  AWS   CLI    │     │   FASTAPI    │    │   OPENAI     │
         │               │     │  WEBSOCKET   │    │    API       │
         │aws ce get-cost|     |              |    |              | 
         |and usage      │     │  (Progress)  │    │              │
         │ list --rg     │     └──────┬───────┘    │ Cost Analysis│
         └──────┬──────--┘            :            └──────┬───────┘
                :                     : Live updates      :
                ▼                     ▼                   :
         ┌─────────────-┐   ┌───────────────┐             :
         │   Active AWS |   │   REACT       │             :
         │ Services only│   │  (Progress    │             :
         │              │   |   Tracker)    │             :
         └─────────────-|   └───────────────┘             :
                                                          ▼
                                                 ┌──────────────┐
                                                 │    AWS RDS   │
                                                 │  POSTGRESQL  │
                                                 │              │
                                                 │              │
                                                 │ · users      │
                                                 │ · analyses   │
                                                 └──────┬───────┘
                                                        :
                                                        : Stored results
                                                        ▼
                                                 ┌───────────────┐
                                                 │    REACT      │
                                                 │ (Final Report │
                                                 │  + Suggestions│
                                                 │  + Fixes)     │
                                                 └───────────────┘
```

## Request Flow

```
①  User ─·─·─► React ─·─·─► FastAPI Auth ─·─·─► JWT (Azure PostgreSQL)

②  User selects Resource Group ─·─·─► Python Backend

③  Python ─·─·─► AWS CLI (`aws ce get-cost-and-usage`) ─·─·─► Filters for unblended costs

④  Python builds dynamic execution list of active services (e.g., ["AmazonEC2", "AmazonRDS"])

⑤  Python executes CLI `describe` subprocesses *only* for those active services

⑥  Python ─·─·─► FastAPI WebSocket ─·─·─► React (live updates for active components)

⑦  Python ─·─·─► OpenAI API ─·─·─► Precise cost & metadata analysis

⑧  React ◄·─·─·─ Final report with localized optimization suggestions
```

## What It Detects

- **Active Cost Drivers** — Ranks services currently costing money so the AI focuses on the highest expenses   first.
- **Over-provisioned Active Resources** — Running EC2 instances, active RDS databases,Orphaned disks, unattached public IPs, idle load balancers
- **Misconfigurations** — Wrong pricing tiers, missing auto-shutdown, no reserved instances, saving plans etc.
- **Unoptimized Active Storage** — Excessive log retention, no lifecycle policies on blob storage, Active S3 buckets missing lifecycle policies or active EBS volumes utilizing legacy gp2 storage etc.
- **Idle Active Elements** — NAT Gateways, Elastic Load Balancers, or VPN connections that are active and charging hourly, but processing zero throughput.

## Prerequisites

- AWS CLI installed and configured (aws configure).
- IAM Permissions: The IAM user/role must have permission to use Cost Explorer (ce:GetCostAndUsage) alongside the standard resource read permissions.
- An AWS RDS PostgreSQL instance.
- An OpenAI API key
- Python 3.10+
- Node.js 18+

## How to Run

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials
uvicorn main:app --reload --port 9000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## How It Works

1. User signs up / logs in via custom JWT auth (credentials stored in Azure PostgreSQL)
2. User requests a scan for the current billing period.
3. Backend runs a Cost Explorer query via the AWS CLI to extract all services with charges greater than $0.
4. Python parses the JSON response, creating an array of active service strings (e.g., ["Amazon Elastic Compute Cloud - Compute", "Amazon Relational Database Service"]).
4. The tool maps these strings to explicit resource-gathering commands inside a lookup table:Amazon Elastic Compute Cloud - Compute $\rightarrow$ Executes aws ec2 describe-instancesAmazon Relational Database Service $\rightarrow$ Executes aws rds describe-db-instances
5. FastAPI WebSockets stream targeted updates to the React UI (e.g., "Detected active RDS usage. Scanning database engines...").
6. The targeted configuration payload is passed to OpenAI to cross-reference the active cost footprint with resource configuration data.
7. Final report with cost breakdown, suggestions, and fix commands is displayed
