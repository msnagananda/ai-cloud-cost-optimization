import json
import os

import ollama

_SYSTEM_PROMPT = """You are an expert AWS cloud cost optimization engineer.
You will be given a JSON payload describing active AWS resources discovered in a customer's account.
Your job is to analyze the infrastructure and identify cost optimization opportunities.

Analyze for:
- Over-provisioned resources (instances/DBs sized larger than needed)
- Idle or unused resources (stopped instances still paying for EBS, unattached volumes, idle LBs/NAT gateways)
- Legacy generation pricing tiers (gp2 vs gp3 EBS, t2 vs t3/t4g EC2, old RDS engine versions)
- Misconfigurations (missing reserved instances/savings plans, no auto-shutdown, public RDS, missing lifecycle policies)
- Redundant or unnecessary spend

Respond ONLY with a valid JSON object matching this exact schema:
{
  "summary": "<2-3 sentence executive summary of the cost posture>",
  "total_estimated_monthly_savings_usd": <number>,
  "issues": [
    {
      "severity": "high" | "medium" | "low",
      "resource_type": "<e.g. EC2 Instance>",
      "resource_id": "<id>",
      "issue": "<concise description of the problem>",
      "estimated_monthly_savings_usd": <number or null>,
      "remediation": "<plain-English action to take>",
      "cli_commands": ["<aws cli command 1>", "<aws cli command 2>"]
    }
  ]
}

Rules:
- cli_commands must be real, executable AWS CLI commands. Use placeholder values like <instance-id> where the user must substitute their actual resource ID.
- If no CLI command applies, use an empty array.
- Sort issues by severity: high first, then medium, then low.
- Be conservative with savings estimates — use documented AWS pricing as a reference.
- If the resource list is empty, return a summary noting no active resources were found and an empty issues array."""


def _build_user_prompt(scan_result: dict) -> str:
    region = scan_result.get("region", "unknown")
    active_services = scan_result.get("active_services", [])
    resources = scan_result.get("resources", [])

    return (
        f"AWS Region: {region}\n"
        f"Active billing services this month: {', '.join(active_services) or 'none detected'}\n"
        f"Total resources scanned: {len(resources)}\n\n"
        f"Resource inventory:\n{json.dumps(resources, indent=2, default=str)}"
    )


class AIAnalyzerError(Exception):
    pass


class AIAnalyzerConnectionError(AIAnalyzerError):
    pass


def analyze(scan_result: dict) -> dict:
    model = os.getenv("OLLAMA_MODEL", "llama3")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    client = ollama.Client(host=host)

    try:
        response = client.chat(
            model=model,
            format="json",
            options={"temperature": 0.2},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(scan_result)},
            ],
        )
    except ollama.ResponseError as e:
        if "model" in str(e).lower() and "not found" in str(e).lower():
            raise AIAnalyzerError(
                f"OLLAMA model '{model}' is not installed. "
                f"Run: ollama pull {model}"
            )
        raise AIAnalyzerError(f"OLLAMA error: {e}")
    except Exception as e:
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            raise AIAnalyzerConnectionError(
                f"Could not connect to OLLAMA at {host}. "
                "Make sure OLLAMA is running: ollama serve"
            )
        raise AIAnalyzerError(f"Unexpected error calling OLLAMA: {e}")

    raw = response.message.content
    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        raise AIAnalyzerError(f"OLLAMA returned non-JSON response: {raw[:200]}")

    analysis["region"] = scan_result.get("region")
    analysis["active_services"] = scan_result.get("active_services", [])
    analysis["total_resources_scanned"] = scan_result.get("total_resources", 0)

    return analysis
