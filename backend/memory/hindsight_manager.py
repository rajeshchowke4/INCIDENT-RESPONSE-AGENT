import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.memory.seed_data import INITIAL_POST_MORTEMS

logger = logging.getLogger("hindsight_manager")

class LocalHindsightFallback:
    """
    High-fidelity local memory bank that mirrors Hindsight's
    retain/recall/reflect semantics when running offline or before
    the user enters their Hindsight Cloud API key.
    """
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memories: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading local memory cache: {e}")
                self.memories = []
        else:
            self.memories = []

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving local memory cache: {e}")

    def retain(self, content: str, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        item_id = f"mem-{len(self.memories) + 1:04d}-{int(datetime.now().timestamp())}"
        record = {
            "id": item_id,
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "metadata": metadata or {},
            "tags": tags or []
        }
        self.memories.append(record)
        self._save()
        return {"status": "success", "id": item_id, "retained_count": len(self.memories)}

    def recall(self, query: str, tags: Optional[List[str]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.memories:
            return []
        
        query_words = set(re.findall(r"\w+", query.lower()))
        scored_results = []

        for mem in self.memories:
            content_str = (mem.get("content", "") + " " + " ".join(mem.get("tags", []))).lower()
            meta_str = json.dumps(mem.get("metadata", {})).lower()
            total_text = f"{content_str} {meta_str}"
            
            # Simple keyword + tag overlap scoring
            score = 0
            for word in query_words:
                if len(word) > 2 and word in total_text:
                    score += 1.5 if word in mem.get("tags", []) else 1.0

            # Match telemetry signatures if stored in metadata
            signatures = mem.get("metadata", {}).get("telemetry_signatures", [])
            for sig in signatures:
                if sig.lower() in query.lower():
                    score += 5.0  # High weight for exact telemetry signature matches

            if score > 0:
                scored_results.append({
                    "id": mem.get("id"),
                    "score": round(score, 3),
                    "content": mem.get("content"),
                    "metadata": mem.get("metadata", {}),
                    "tags": mem.get("tags", []),
                    "timestamp": mem.get("timestamp")
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:limit]


class HindsightMemoryManager:
    """
    Manager for Vectorize Hindsight long-term agent memory.
    Connects to Hindsight Cloud / self-hosted instance, with seamless
    fallback to persistent local memory engine.
    """
    def __init__(self):
        self.base_url = settings.HINDSIGHT_BASE_URL
        self.api_key = settings.HINDSIGHT_API_KEY
        self.bank_id = settings.HINDSIGHT_BANK_ID
        self.client = None
        self.local_fallback = LocalHindsightFallback(
            Path(__file__).parent.parent.parent / "data" / "local_hindsight_bank.json"
        )
        self._init_client()
        self.seed_initial_knowledge_if_empty()

    def _init_client(self):
        if self.api_key:
            try:
                from hindsight_client import Hindsight
                self.client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
                logger.info(f"Initialized Hindsight Client connecting to {self.base_url}")
            except Exception as e:
                logger.warning(f"Could not connect to Hindsight Cloud: {e}. Using local fallback engine.")
                self.client = None
        else:
            logger.info("No HINDSIGHT_API_KEY found in environment. Using local persistent Hindsight bank.")
            self.client = None

    def update_credentials(self, api_key: str, base_url: Optional[str] = None, bank_id: Optional[str] = None):
        """Allows hot-updating Hindsight credentials from UI"""
        self.api_key = api_key.strip()
        if base_url:
            self.base_url = base_url.strip()
        if bank_id:
            self.bank_id = bank_id.strip()
        self._init_client()
        if self.client:
            self.seed_initial_knowledge_if_empty()
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        is_cloud = self.client is not None and bool(self.api_key)
        connection_ok = False
        message = ""
        
        if is_cloud:
            try:
                # Test connectivity
                version = self.client.get_version()
                connection_ok = True
                message = f"Connected to Hindsight Cloud (v{getattr(version, 'version', 'active')})"
            except Exception as e:
                connection_ok = False
                message = f"Hindsight Cloud key configured, but ping failed: {e}. Active fallback in place."
        else:
            connection_ok = True
            message = "Operating with Local Persistent Memory Bank (Enter Hindsight Cloud Key + promo MEMHACK99 for cloud sync)"

        return {
            "mode": "cloud" if is_cloud else "local_fallback",
            "is_connected": connection_ok,
            "base_url": self.base_url,
            "bank_id": self.bank_id,
            "has_api_key": bool(self.api_key),
            "message": message,
            "total_memories": len(self.list_all_memories())
        }

    def seed_initial_knowledge_if_empty(self):
        """Seeds historical post-mortems so the agent starts with institutional knowledge"""
        existing = self.list_all_memories()
        if len(existing) == 0:
            logger.info("Seeding initial institutional post-mortems into Hindsight memory...")
            for post_mortem in INITIAL_POST_MORTEMS:
                self.retain_post_mortem(post_mortem)

    def retain_post_mortem(self, pm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retains a verified post-mortem into Hindsight memory bank.
        """
        content_lines = [
            f"# Post-Mortem Incident: {pm_data.get('id', 'INC-UNKNOWN')} - {pm_data.get('title', '')}",
            f"Service: {pm_data.get('service', 'unknown')} | Severity: {pm_data.get('severity', 'P1')} | Date: {pm_data.get('date', '')}",
            f"\n## Summary:\n{pm_data.get('summary', '')}",
            f"\n## Root Cause:\n{pm_data.get('root_cause', '')}",
            "\n## Failed Attempts (What NOT to do):\n" + "\n".join(f"- {item}" for item in pm_data.get("failed_attempts", [])),
            "\n## Verified Mitigation & Runbook Steps:\n" + "\n".join(f"- {step}" for step in pm_data.get("verified_mitigation", [])),
            f"\n## Telemetry Signatures:\n" + ", ".join(pm_data.get("telemetry_signatures", []))
        ]
        full_text = "\n".join(content_lines)

        metadata = {
            "incident_id": pm_data.get("id"),
            "service": pm_data.get("service"),
            "severity": pm_data.get("severity"),
            "root_cause": pm_data.get("root_cause"),
            "telemetry_signatures": pm_data.get("telemetry_signatures", []),
            "date": pm_data.get("date")
        }
        tags = pm_data.get("tags", [])

        # Always save to local fallback for persistent redundancy
        self.local_fallback.retain(content=full_text, metadata=metadata, tags=tags)

        # Retain into Hindsight Cloud if available
        if self.client:
            try:
                resp = self.client.retain(
                    bank_id=self.bank_id,
                    content=full_text,
                    metadata={k: str(v) for k, v in metadata.items() if isinstance(v, (str, int, float))},
                    tags=tags
                )
                logger.info(f"Retained incident {pm_data.get('id')} to Hindsight Cloud: {resp}")
            except Exception as e:
                logger.error(f"Failed to retain to Hindsight Cloud: {e}")

        return {"status": "retained", "incident_id": pm_data.get("id")}

    def recall_relevant_incidents(self, query: str, service: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Recalls historical incidents matching the telemetry or query.
        """
        search_query = f"{service or ''} {query}".strip()
        
        # 1. Try Hindsight Cloud client if available
        if self.client:
            try:
                resp = self.client.recall(
                    bank_id=self.bank_id,
                    query=search_query,
                    max_tokens=4096
                )
                # Parse Hindsight response
                formatted = []
                # Check for results or to_dict
                results = getattr(resp, "results", None) or []
                for item in results:
                    formatted.append({
                        "content": getattr(item, "text", getattr(item, "content", str(item))),
                        "score": getattr(item, "score", 0.95),
                        "metadata": getattr(item, "metadata", {})
                    })
                if formatted:
                    return formatted
            except Exception as e:
                logger.warning(f"Hindsight Cloud recall failed ({e}), using local memory bank.")

        # 2. Use local fallback recall
        return self.local_fallback.recall(query=search_query, tags=tags, limit=4)

    def list_all_memories(self) -> List[Dict[str, Any]]:
        """Returns all currently retained memories for visualization"""
        return self.local_fallback.memories

    def clear_all(self):
        """Resets memory bank"""
        self.local_fallback.memories = []
        self.local_fallback._save()
        self.seed_initial_knowledge_if_empty()

# Global singleton
memory_manager = HindsightMemoryManager()
