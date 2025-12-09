"""Background worker for correlating logs with TTP intelligence."""
import hashlib
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.models import LogEntry, Server
from src.db.repository.alert_repo import create_alert
from src.db.setup import SessionLocal
from src.utils.log_parser import parse_log_line
from src.workers.ttp_engine import TTPEngine


class TTPWorker:
    """Continuously evaluates new logs against the TTP engine."""

    def __init__(
        self,
        intelligence_dir: str = "./TTP_Intelligence",
        poll_interval: float = 7.5,
        batch_size: int = 100
    ) -> None:
        self.intelligence_dir = intelligence_dir
        self.poll_interval = poll_interval
        self.batch_size = batch_size

        self.engine = TTPEngine(intelligence_dir)
        self.engine.load_ttps()

        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._last_processed_id = 0

        self.stats: Dict[str, Any] = {
            "logs_evaluated": 0,
            "alerts_generated": 0,
            "last_run": None,
            "last_reload": datetime.utcnow().isoformat(),
            "engine": self.engine.get_stats(),
        }

    # Public API -----------------------------------------------------------------

    def start(self) -> None:
        if self.running:
            print("[TTPWorker] Already running")
            return

        self.running = True
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
        print("[TTPWorker] Started background thread")

    def run(self) -> None:
        print("[TTPWorker] Starting main loop")
        self._last_processed_id = self._get_latest_log_id()
        print(f"[TTPWorker] Initial checkpoint set to log ID {self._last_processed_id}")

        try:
            while self.running:
                processed = self._process_batch()
                self.stats["last_run"] = datetime.utcnow().isoformat()

                if processed == 0:
                    time.sleep(self.poll_interval)
                else:
                    time.sleep(0.1)
        except Exception as exc:
            print(f"[TTPWorker] Fatal error: {exc}")
            traceback.print_exc()
        finally:
            self.running = False
            print("[TTPWorker] Loop exited")

    def stop(self) -> None:
        if not self.running:
            return
        print("[TTPWorker] Stopping...")
        self.running = False
        if self._thread:
            self._thread.join(timeout=self.poll_interval * 2)
            self._thread = None
        print("[TTPWorker] Stopped")

    def reload_intelligence(self) -> Dict[str, Any]:
        print("[TTPWorker] Reloading TTP intelligence...")
        total = self.engine.load_ttps()
        self.stats["engine"] = self.engine.get_stats()
        self.stats["last_reload"] = datetime.utcnow().isoformat()
        return {"patterns_loaded": total, "stats": self.stats["engine"]}

    def is_running(self) -> bool:
        return self.running

    def get_stats(self) -> Dict[str, Any]:
        payload = dict(self.stats)
        payload["engine"] = self.engine.get_stats()
        payload["running"] = self.running
        payload["last_processed_id"] = self._last_processed_id
        return payload

    # Internal helpers -----------------------------------------------------------

    def _process_batch(self) -> int:
        logs = self._get_unprocessed_logs()
        if not logs:
            return 0

        processed = 0
        for log in logs:
            try:
                matches = self.engine.match_log(log)
                if matches:
                    for match in matches:
                        self._store_alert(log, match)
                        self.stats["alerts_generated"] += 1
                processed += 1
                self.stats["logs_evaluated"] += 1
                self._last_processed_id = max(self._last_processed_id, log["id"])
            except Exception as exc:
                print(f"[TTPWorker] Error processing log {log.get('id')}: {exc}")
                traceback.print_exc()
        return processed

    def _get_unprocessed_logs(self) -> List[Dict[str, Any]]:
        session = SessionLocal()
        try:
            query = (
                session.query(LogEntry, Server)
                .join(Server, LogEntry.server_id == Server.id, isouter=True)
                .filter(LogEntry.id > self._last_processed_id)
                .order_by(LogEntry.id.asc())
                .limit(self.batch_size)
            )

            logs: List[Dict[str, Any]] = []
            for entry, server in query.all():
                parsed = parse_log_line(entry.log_source, entry.content)
                normalized = parsed.get("normalized", {}) if isinstance(parsed, dict) else {}
                fields = parsed.get("fields", {}) if isinstance(parsed, dict) else {}

                logs.append({
                    "id": entry.id,
                    "server_id": entry.server_id,
                    "timestamp": entry.recv_time.isoformat() if entry.recv_time else None,
                    "log_type": entry.log_source,
                    "raw_line": entry.content,
                    "raw_line_lower": entry.content.lower(),
                    "hostname": server.hostname if server else None,
                    "ip_address": server.ip_address if server else None,
                    "parsed_data": fields,
                    "normalized_fields": normalized,
                })

            return logs
        finally:
            session.close()

    def _store_alert(self, log: Dict[str, Any], match: Dict[str, Any]) -> None:
        severity = (match.get("severity") or "medium").lower()
        if severity not in {"low", "medium", "high", "critical"}:
            severity = "medium"

        rule_fingerprint = f"{match.get('ttp_id')}::{match.get('pattern_id')}"
        rule_hash = int(hashlib.sha1(rule_fingerprint.encode("utf-8")).hexdigest()[:8], 16)

        metadata = {
            "source": "ttp_engine",
            "match": match,
            "log_context": {
                "id": log.get("id"),
                "hostname": log.get("hostname"),
                "ip_address": log.get("ip_address"),
                "timestamp": log.get("timestamp"),
            },
        }

        create_alert(
            log_entry_id=log.get("id"),
            server_id=log.get("server_id"),
            rule_id=rule_hash,
            severity=severity,
            title=match.get("title", "TTP Match"),
            description=match.get("description", ""),
            metadata=metadata
        )

    def _get_latest_log_id(self) -> int:
        session = SessionLocal()
        try:
            latest = session.query(LogEntry.id).order_by(LogEntry.id.desc()).first()
            return latest[0] if latest else 0
        finally:
            session.close()
