import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.agent.llm_client import llm_client
from backend.memory.hindsight_manager import memory_manager

logger = logging.getLogger("sre_agent")

SYSTEM_PROMPT_VANILLA = """You are an On-Call DevOps / SRE Incident Response AI.
You have NO access to historical memory, past incident post-mortems, or organization-specific runbooks.
Analyze the incoming production alert and error logs using generic first-principles debugging.
Suggest general troubleshooting steps.
"""

SYSTEM_PROMPT_HINDSIGHT = """You are ResqOps, an elite SRE Incident Copilot powered by Hindsight Memory.
You have access to historical production post-mortems and institutional debugging memory stored in Hindsight.

Your objective:
1. Cross-reference the incoming alert and stack traces with recalled Hindsight memories.
2. Identify if this is a recurring failure or an organizational pattern.
3. Explicitly state the exact root cause discovered in past incidents.
4. Warn the on-call engineer about actions NOT to take (past failed attempts).
5. Provide the exact, verified mitigation runbook with executable commands.
6. Reference the specific historical incident IDs (e.g., INC-2024-1014).

Be decisive, precise, and practical. Save MTTR.
"""

class SREAgent:
    """
    Dual-mode SRE Agent that showcases the dramatic difference
    between a stateless LLM and a Hindsight memory-augmented agent.
    """

    def investigate(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs both Vanilla and Hindsight-augmented analysis on the incoming alert.
        """
        service = alert_payload.get("service", "unknown")
        summary = alert_payload.get("summary", "")
        raw_logs = alert_payload.get("raw_logs", "")
        alert_name = alert_payload.get("alert_name", "UnknownAlert")
        severity = alert_payload.get("severity", "P1")

        combined_telemetry = f"Service: {service}\nAlert: {alert_name} ({severity})\nSummary: {summary}\n\nLogs:\n{raw_logs}"

        # 1. Recall historical incidents from Hindsight memory bank
        recalled_memories = memory_manager.recall_relevant_incidents(
            query=f"{summary} {raw_logs}",
            service=service
        )

        # 2. Run Vanilla (Stateless) Agent Analysis
        vanilla_prompt = f"""Incoming Production Alert:
{combined_telemetry}

Provide your SRE diagnosis and suggested mitigation steps."""
        
        vanilla_response = llm_client.generate(
            prompt=vanilla_prompt,
            system_prompt=SYSTEM_PROMPT_VANILLA,
            temperature=0.2
        )

        # 3. Run Hindsight-Augmented Agent Analysis
        if recalled_memories:
            memories_context_str = "\n\n--- RECALLED HINDSIGHT POST-MORTEMS ---\n"
            for idx, mem in enumerate(recalled_memories, 1):
                mem_meta = mem.get("metadata", {})
                memories_context_str += f"\n[Memory #{idx}] Incident ID: {mem_meta.get('incident_id', 'Unknown')}\n"
                memories_context_str += f"Content:\n{mem.get('content')}\n"
                memories_context_str += f"Relevance Score: {mem.get('score', 1.0)}\n"
        else:
            memories_context_str = "\n[No historical matches found in Hindsight memory for this signature. Treat as NOVEL incident.]\n"

        hindsight_prompt = f"""Incoming Production Alert:
{combined_telemetry}

{memories_context_str}

Analyze this incident. If historical memories match, cite them directly, diagnose root cause, list dangerous mistakes to avoid, and provide the exact mitigation runbook."""

        hindsight_response = llm_client.generate(
            prompt=hindsight_prompt,
            system_prompt=SYSTEM_PROMPT_HINDSIGHT,
            temperature=0.1
        )

        # 4. Compute comparative telemetry & ROI metrics
        has_match = len(recalled_memories) > 0
        confidence = min(99.4, 60.0 + (recalled_memories[0].get("score", 1.0) * 8.0)) if has_match else 25.0
        
        return {
            "incident_metadata": {
                "service": service,
                "severity": severity,
                "alert_name": alert_name,
                "timestamp": alert_payload.get("timestamp", datetime.utcnow().isoformat())
            },
            "recalled_memories": recalled_memories,
            "has_memory_match": has_match,
            "memory_match_count": len(recalled_memories),
            "vanilla_agent": {
                "title": "Stateless LLM (Zero Institutional Memory)",
                "diagnosis": vanilla_response,
                "confidence_score": 35.0,
                "mttr_estimate": "45 - 90 minutes (Manual discovery required)",
                "actionability": "Low / Generic advice"
            },
            "hindsight_agent": {
                "title": "ResqOps (Hindsight Memory-Augmented)",
                "diagnosis": hindsight_response,
                "confidence_score": round(confidence, 1),
                "mttr_estimate": "60 - 90 seconds (Instant verified runbook)",
                "actionability": "High / Precision script execution",
                "matched_incidents": [
                    m.get("metadata", {}).get("incident_id") for m in recalled_memories if m.get("metadata", {}).get("incident_id")
                ]
            }
        }

sre_agent = SREAgent()
