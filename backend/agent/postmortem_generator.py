import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.agent.llm_client import llm_client
from backend.memory.hindsight_manager import memory_manager

logger = logging.getLogger("postmortem_generator")

POSTMORTEM_SYSTEM_PROMPT = """You are an elite Site Reliability Engineering (SRE) Post-Mortem Facilitator.
Your goal is to generate a comprehensive, Blameless Post-Mortem Report from an incident's telemetry, resolution steps, and developer notes.

You must output a structured JSON with:
{
  "id": "INC-YYYY-MMDD",
  "service": "affected-service-name",
  "severity": "P0 | P1 | P2",
  "title": "Clear concise incident title",
  "date": "YYYY-MM-DD",
  "summary": "2-3 sentence overview of impact and downtime",
  "root_cause": "Deep technical explanation of the primary root cause",
  "failed_attempts": ["List of actions that did NOT work or made things worse"],
  "verified_mitigation": ["Step-by-step commands or actions that successfully fixed the incident"],
  "tags": ["relevant", "keywords", "for", "hindsight", "indexing"],
  "telemetry_signatures": ["Exact error substrings, stack trace identifiers, or exception names"]
}
Output ONLY valid raw JSON with no conversational preamble.
"""

class PostMortemGenerator:
    """
    Synthesizes blameless post-mortems and automatically commits
    them to Hindsight memory bank to continuously expand institutional intelligence.
    """

    def generate_and_retain(
        self,
        service: str,
        title: str,
        severity: str,
        summary: str,
        raw_logs: str,
        resolution_notes: str,
        failed_attempts_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a structured post-mortem and retains it into Hindsight.
        """
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        incident_id = f"INC-{datetime.utcnow().strftime('%Y-%m%d-%H%M')}"

        prompt = f"""Generate a Blameless Post-Mortem JSON:
Incident ID: {incident_id}
Date: {today_str}
Service: {service}
Severity: {severity}
Title: {title}
Summary of impact: {summary}

Error Logs / Telemetry:
{raw_logs}

Resolution Notes (What actually fixed it):
{resolution_notes}

Failed Attempts Notes (What didn't work):
{failed_attempts_notes or 'None specified'}
"""

        response_text = llm_client.generate(
            prompt=prompt,
            system_prompt=POSTMORTEM_SYSTEM_PROMPT,
            temperature=0.1
        )

        # Parse or create structured post-mortem
        try:
            # Clean possible markdown json wrapper
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            pm_data = json.loads(cleaned.strip())
        except Exception as e:
            logger.warning(f"Could not parse LLM post-mortem as JSON: {e}. Building fallback structured record.")
            # Fallback structured construction
            pm_data = {
                "id": incident_id,
                "service": service,
                "severity": severity,
                "title": title,
                "date": today_str,
                "summary": summary,
                "root_cause": resolution_notes,
                "failed_attempts": [failed_attempts_notes] if failed_attempts_notes else ["Generic restart without inspecting dependencies"],
                "verified_mitigation": [f"1. {resolution_notes}", "2. Monitored health metrics for stability"],
                "tags": [service, severity.lower(), "post-mortem", "auto-generated"],
                "telemetry_signatures": [s.strip() for s in raw_logs.splitlines() if len(s.strip()) > 10][:3]
            }

        # Retain into Hindsight Memory Bank
        retain_result = memory_manager.retain_post_mortem(pm_data)

        return {
            "post_mortem": pm_data,
            "retain_status": retain_result,
            "total_memories": len(memory_manager.list_all_memories())
        }

postmortem_generator = PostMortemGenerator()
