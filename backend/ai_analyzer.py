import json
import os

from openai import OpenAI, AuthenticationError, PermissionDeniedError, APIConnectionError

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


class AIAnalyzerAuthError(AIAnalyzerError):
    pass


class AIAnalyzerConnectionError(AIAnalyzerError):
    pass


def analyze(scan_result: dict) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIAnalyzerAuthError(
            "OPENAI_API_KEY environment variable is not set. "
            "Add it to your .env file and restart the server."
        )

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(scan_result)},
            ],
            temperature=0.2,
        )
    except AuthenticationError:
        raise AIAnalyzerAuthError(
            "Invalid OpenAI API key. Check your OPENAI_API_KEY in .env."
        )
    except PermissionDeniedError:
        raise AIAnalyzerAuthError(
            "OpenAI API key does not have permission to use gpt-4o. "
            "Ensure your account has access to the model."
        )
    except APIConnectionError as e:
        raise AIAnalyzerConnectionError(
            f"Could not connect to OpenAI API: {e}"
        )

    raw = response.choices[0].message.content
    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        raise AIAnalyzerError(f"OpenAI returned non-JSON response: {raw[:200]}")

    # Merge scan metadata into the final response
    analysis["region"] = scan_result.get("region")
    analysis["active_services"] = scan_result.get("active_services", [])
    analysis["total_resources_scanned"] = scan_result.get("total_resources", 0)

    return analysis
