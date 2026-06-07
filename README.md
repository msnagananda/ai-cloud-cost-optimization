# AI Cloud Cost Detective

An AI-powered tool that investigates AWS cloud costs automatically. It scans resources in an AWS Account / Region, detects cost issues like over-provisioning and misconfigurations, and provides actionable suggestions with fixes.

### 🚀 ** Youtube video link **
[**aws cost optimizer tool**](https://youtu.be/f789NiDvE6k)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite + TypeScript + Tailwind) |
| Backend | Python (FastAPI) |
| Auth | Custom JWT Auth (bcrypt + PyJWT) |
| Cloud Data | Aws CLI |
| Cloud | Aws |
| AI Analysis | OLLAMA API |
| Database | Dockerized PostgreSQL |
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
         │  AWS   CLI    │     │   FASTAPI    │    │   OOLAMA     │
         │               │     │  WEBSOCKET   │    │    API       │
         │aws ce get-cost|     |              |    |              | 
         |               │     │  (Progress)  │    │              │
         │               │     └──────┬───────┘    │ Cost Analysis│
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
                                                 │  Dockerized  │
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
①  User ─·─·─► React ─·─·─► FastAPI Auth ─·─·─► JWT (PostgreSQL)

②  User selects Resource Group ─·─·─► Python Backend

③  Python ─·─·─► AWS CLI (`aws ce get-cost-and-usage`) ─·─·─► Filters for unblended costs

④  Python builds dynamic execution list of active services (e.g., ["AmazonEC2", "AmazonRDS"])

⑤  Python executes CLI `describe` subprocesses *only* for those active services

⑥  Python ─·─·─► FastAPI WebSocket ─·─·─► React (live updates for active components)

⑦  Python ─·─·─► OOLAMA API ─·─·─► Precise cost & metadata analysis

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
- An OOLAMA installed
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

1. User signs up / logs in via custom JWT auth (credentials stored in PostgreSQL)
2. User requests a scan for the current billing period.
3. Backend runs a Cost Explorer query via the AWS CLI to extract all services with charges greater than $0.
4. Python parses the JSON response, creating an array of active service strings (e.g., ["Amazon Elastic Compute Cloud - Compute", "Amazon Relational Database Service"]).
4. The tool maps these strings to explicit resource-gathering commands inside a lookup table:Amazon Elastic Compute Cloud - Compute $\rightarrow$ Executes aws ec2 describe-instancesAmazon Relational Database Service $\rightarrow$ Executes aws rds describe-db-instances
5. FastAPI WebSockets stream targeted updates to the React UI (e.g., "Detected active RDS usage. Scanning database engines...").
6. The targeted configuration payload is passed to OOLAMA to cross-reference the active cost footprint with resource configuration data.
7. Final report with cost breakdown, suggestions, and fix commands is displayed

## My Udemy Courses:

### 🚀 **DevSecOps**
- Learn the essentials of DevSecOps and how security integrates with the DevOps pipeline.  
[**DevSecOps Course**](https://tinyurl.com/2p8dxbwn)

### 🚀 **DevSecOps Fundamentals**
- A foundational course covering the core concepts of DevSecOps for beginners.  
[**DevSecOps Fundamentals**](https://shorturl.at/H9kqG)

### 🚀 **SonarQube**
- Master SonarQube to analyze and improve the quality of your code with automated security checks.  
[**SonarQube Course**](https://tinyurl.com/mzfukn4p)

### 🚀 **Serverless**
- Dive into serverless architectures and build efficient, scalable applications.  
[**Serverless Course**](https://tinyurl.com/st5xde5z)

### 🚀 **Docker**
- Learn Docker, containerization, and Kubernetes to run your apps in any environment effortlessly.  
[**Docker Course**](https://tinyurl.com/2ffv8yjn)

### 🚀 **CI/CD Jenkins Master**
- Master Jenkins and automate your software build and delivery pipeline.  
[**Jenkins Master Course**](https://rb.gy/u0ygq)

### 🚀 **Free Linux Course: Introduction to Linux Crash Course**
- Get started with Linux, the backbone of many modern IT systems.  
[**Linux Crash Course**](https://www.udemy.com/course/introduction-to-linux-crash-course)

### 🚀 **AWS DevOps Certification: DOP-C01 Practice Test**
- Prepare for the AWS DevOps Engineer - Professional exam with this practice test.  
[**AWS DevOps Practice Test**](https://www.udemy.com/course/aws-devops-practice-test/?referralCode=D8209AD57D310A001C78)

