# Prompt 2: OLAMA API Integration for Cost Analysis

Build on top of the existing FastAPI backend. Add AI-powered cost analysis using the OLLAMA  directly.

## What to build

- Create an `ai_analyzer.py` module in `backend/` that:
  - Takes the list of AWS resources (from `aws_scanner.py`) as input.
  - Builds a prompt asking the AI to analyze the active infrastructure for: over-provisioning, idle/unused resources, misconfigurations, legacy generation pricing tiers (e.g., gp2 vs gp3, t2 vs t3), and cost optimization opportunities.
  - Calls the OLLAMA chat completions API (`gpt-4o`) and returns the structured analysis.
- The AI response should include: a summary, a list of issues found (with severity: high/medium/low), estimated monthly savings, and actionable remediation commands (AWS CLI commands or fallback configuration adjustments that the user can execute directly).
- Update `POST /api/analyze` to call `aws_scanner` first, then pass results to `ai_analyzer`, and return the final analysis.
- Store the OLLAMA API key in environment variables. Add a `.env.example` file.
- Update `requirements.txt` — add `ollama`, `python-dotenv`.

## Project structure update

```
backend/
├── main.py          (updated)
├── aws_scanner.py (no change)
├── ai_analyzer.py   (new)
├── requirements.txt (updated)
├── .env.example     (new — OLLAMA)
```

Refer to Architecture.MD and RequestFlow.MD. This covers steps ⑤ and ⑥ of the updated request flow.
