"""TTP Intelligence Engine for matching logs against MITRE ATT&CK patterns."""
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TTPPattern:
    """Represents a single detection pattern derived from MITRE ATT&CK TTP JSON."""

    ttp_id: str
    pattern_id: str
    name: str
    log_source: str
    severity: str
    tactic: str
    technique: str
    description: str
    conditions: Dict[str, Any]
    raw_pattern: Dict[str, Any]
    references: List[str]
    data_sources: List[str]
    file_path: str


class TTPEngine:
    """Loads TTP intelligence JSON files and matches log entries."""

    def __init__(self, intelligence_dir: str = "./TTP_Intelligence"):
        self.intelligence_dir = Path(intelligence_dir)
        self.patterns: Dict[str, List[TTPPattern]] = defaultdict(list)
        self.total_patterns: int = 0
        self.loaded_files: List[str] = []

    def load_ttps(self) -> int:
        """Load all TTP definitions from the intelligence directory."""
        self.patterns.clear()
        self.total_patterns = 0
        self.loaded_files = []

        if not self.intelligence_dir.exists():
            print(f"[TTPEngine] Intelligence directory not found: {self.intelligence_dir}")
            return 0

        loaded = 0
        for json_file in sorted(self.intelligence_dir.rglob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except Exception as exc:
                print(f"[TTPEngine] Failed to load {json_file}: {exc}")
                continue

            ttps = data.get("ttps", []) if isinstance(data, dict) else []
            for ttp in ttps:
                severity = (ttp.get("severity") or "medium").lower()
                tactic = ttp.get("tactic", "Unknown")
                technique = ttp.get("technique", "Unknown")
                description = ttp.get("description", "")
                references = ttp.get("references") or ttp.get("data_sources") or []

                detection_patterns = ttp.get("detection_patterns", [])
                for pattern in detection_patterns:
                    log_source = (pattern.get("log_source") or ttp.get("log_sources", ["any"])[0]).lower()
                    conditions = pattern.get("conditions", {}) or {}
                    pattern_id = pattern.get("pattern_id", f"{ttp.get('ttp_id')}_pattern")
                    name = pattern.get("name", f"Detection for {technique}")

                    ttp_pattern = TTPPattern(
                        ttp_id=ttp.get("ttp_id", "UNKNOWN"),
                        pattern_id=pattern_id,
                        name=name,
                        log_source=log_source,
                        severity=severity,
                        tactic=tactic,
                        technique=technique,
                        description=description,
                        conditions=conditions,
                        raw_pattern=pattern,
                        references=references if isinstance(references, list) else [references],
                        data_sources=ttp.get("data_sources", []),
                        file_path=str(json_file)
                    )

                    self.patterns[log_source].append(ttp_pattern)
                    loaded += 1

            self.loaded_files.append(str(json_file))

        self.total_patterns = loaded
        print(f"[TTPEngine] Loaded {loaded} detection patterns across {len(self.loaded_files)} files")
        return loaded

    def match_log(self, log_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match a log entry against loaded TTP patterns."""
        if not log_entry:
            return []

        log_type = (log_entry.get("log_type") or "").lower()
        candidates: List[TTPPattern] = []

        candidates.extend(self.patterns.get(log_type, []))
        candidates.extend(self.patterns.get("any", []))

        matches: List[Dict[str, Any]] = []
        for pattern in candidates:
            evidence = self._evaluate_pattern(pattern, log_entry)
            if evidence is None:
                continue

            matches.append(self._build_match(pattern, log_entry, evidence))

        return matches

    def _evaluate_pattern(self, pattern: TTPPattern, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        evidence: Dict[str, Any] = {}
        for key, expected in pattern.conditions.items():
            matched, details = self._evaluate_condition(key, expected, log_entry)
            if not matched:
                return None
            if details:
                evidence[key] = details
        return evidence

    def _evaluate_condition(self, key: str, expected: Any, log_entry: Dict[str, Any]) -> Tuple[bool, Optional[Any]]:
        key_lower = key.lower()
        raw_line_lower = log_entry.get("raw_line_lower") or (log_entry.get("raw_line") or "").lower()

        if key_lower == "event_id":
            event_id = self._extract_event_id(log_entry, raw_line_lower)
            if event_id is None:
                return False, None
            values = expected if isinstance(expected, list) else [expected]
            expected_values = set()
            for val in values:
                try:
                    expected_values.add(int(val))
                except (TypeError, ValueError):
                    continue
            if not expected_values:
                return False, None
            return (event_id in expected_values, event_id if event_id in expected_values else None)

        if key_lower == "keywords_any":
            if not isinstance(expected, list):
                expected = [expected]
            matches = [token for token in expected if str(token).lower() in raw_line_lower]
            return (len(matches) > 0, matches if matches else None)

        if key_lower.endswith("_contains_any"):
            field = key_lower.replace("_contains_any", "")
            candidate = self._get_field_text(log_entry, field, raw_line_lower)
            if candidate is None:
                return False, None
            tokens = expected if isinstance(expected, list) else [expected]
            matches = [token for token in tokens if str(token).lower() in candidate]
            return (len(matches) > 0, matches if matches else None)

        if key_lower.endswith("_contains_all"):
            field = key_lower.replace("_contains_all", "")
            candidate = self._get_field_text(log_entry, field, raw_line_lower)
            if candidate is None:
                return False, None
            tokens = expected if isinstance(expected, list) else [expected]
            for token in tokens:
                if str(token).lower() not in candidate:
                    return False, None
            return True, tokens

        # Generic equality / membership check
        candidate_value = self._get_field_value(log_entry, key_lower)
        if candidate_value is None:
            return False, None

        if isinstance(expected, list):
            for value in expected:
                if self._compare_values(candidate_value, value):
                    return True, candidate_value
            return False, None

        if self._compare_values(candidate_value, expected):
            return True, candidate_value

        return False, None

    def _get_field_value(self, log_entry: Dict[str, Any], field: str) -> Optional[Any]:
        normalized = log_entry.get("normalized_fields") or {}
        if field in normalized:
            return normalized[field]

        parsed = log_entry.get("parsed_data")
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                if key.lower() == field:
                    return value

        if field in log_entry:
            return log_entry[field]

        # Fallbacks for common aliases
        if field == "uri":
            return normalized.get("request_uri") or normalized.get("uri")
        if field in ("message", "raw_message"):
            return normalized.get("message") or normalized.get("raw_message") or log_entry.get("raw_line")

        return None

    def _get_field_text(self, log_entry: Dict[str, Any], field: str, default: str) -> Optional[str]:
        value = self._get_field_value(log_entry, field)
        if value is None:
            return default
        if isinstance(value, (list, tuple, set)):
            value = " ".join(str(item) for item in value)
        return str(value).lower()

    def _extract_event_id(self, log_entry: Dict[str, Any], raw_line_lower: str) -> Optional[int]:
        candidate = self._get_field_value(log_entry, "event_id")
        if candidate is None:
            match = re.search(r"event[_\s]*id\"?\s*[:=]\s*(\d+)", raw_line_lower)
            if match:
                candidate = match.group(1)
        if candidate is None:
            return None
        try:
            return int(candidate)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _compare_values(left: Any, right: Any) -> bool:
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return int(left) == int(right)
        left_str = str(left).lower()
        right_str = str(right).lower()
        return left_str == right_str

    def _build_match(self, pattern: TTPPattern, log_entry: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_name": pattern.name,
            "ttp_id": pattern.ttp_id,
            "technique": pattern.technique,
            "tactic": pattern.tactic,
            "severity": pattern.severity,
            "description": pattern.description,
            "log_type": pattern.log_source,
            "title": f"{pattern.name} ({pattern.ttp_id})",
            "evidence": evidence,
            "conditions": pattern.conditions,
            "references": pattern.references,
            "data_sources": pattern.data_sources,
            "source_file": pattern.file_path,
            "matched_at": datetime.utcnow().isoformat(),
            "log_id": log_entry.get("id"),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_patterns": self.total_patterns,
            "by_log_type": {log_type: len(patterns) for log_type, patterns in self.patterns.items()},
            "loaded_files": self.loaded_files,
            "intelligence_dir": str(self.intelligence_dir)
        }
