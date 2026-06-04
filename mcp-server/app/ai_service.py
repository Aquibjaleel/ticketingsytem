import json
from openai_client import call_model

TICKET_SYSTEM_PROMPT = """
You are an IT support ticket assistant.

Analyze the ticket and return valid JSON only.

Allowed categories:
- Access
- Network
- Hardware
- Software
- Security
- Cloud
- Other

Allowed priorities:
- Low
- Medium
- High
- Critical

Return exactly in this JSON format:
{
  "summary": "User cannot log in after password reset",
  "category": "Access",
  "priority": "Medium"
}
"""

def analyze_ticket(ticket_text: str) -> dict:
    user_prompt = f"Ticket description:\n{ticket_text}"

    ai_text = call_model(TICKET_SYSTEM_PROMPT, user_prompt)

    try:
        return json.loads(ai_text)
    except json.JSONDecodeError:
        return {
            "summary": "AI response could not be parsed",
            "category": "Other",
            "priority": "Low"
        }