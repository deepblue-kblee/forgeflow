"""
Review Checkpoint Cache Manager (Zero-Dependency)

Provides incremental SHA-256 diff caching for static AST code review analysis.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .smell_detector import CodeSmell


class ReviewCacheManager:
    """Manages disk-backed incremental caching of AST code smells by content SHA-256."""

    CACHE_SCHEMA_VERSION = 1
    DEFAULT_CACHE_REL_PATH = Path(".forgeflow") / "cache" / "review_cache.json"

    def __init__(self, repo_root: Path, cache_file: Optional[Path] = None, enabled: bool = True):
        self.repo_root = repo_root.resolve()
        self.cache_file = (cache_file or (self.repo_root / self.DEFAULT_CACHE_REL_PATH)).resolve()
        self.enabled = enabled
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        self.hits = 0
        self.misses = 0

        if self.enabled:
            self._load()

    @staticmethod
    def compute_sha256(content: str | bytes) -> str:
        data = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(data).hexdigest()

    def _get_key(self, file_path: Path) -> str:
        try:
            return str(file_path.resolve().relative_to(self.repo_root))
        except Exception:
            return str(file_path.resolve())

    def _load(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            raw = json.loads(self.cache_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("version") == self.CACHE_SCHEMA_VERSION:
                entries = raw.get("entries", {})
                if isinstance(entries, dict):
                    self._entries = entries
        except Exception:
            # Corrupted cache file: fail-safe by resetting entries
            self._entries = {}

    def get(self, file_path: Path, content: str | bytes) -> Optional[List[CodeSmell]]:
        if not self.enabled:
            return None

        key = self._get_key(file_path)
        entry = self._entries.get(key)
        if not entry or not isinstance(entry, dict):
            self.misses += 1
            return None

        current_digest = self.compute_sha256(content)
        if entry.get("sha256") != current_digest:
            self.misses += 1
            return None

        raw_smells = entry.get("smells", [])
        self.hits += 1
        return [
            CodeSmell(
                file_path=s.get("file_path", str(file_path)),
                line_no=s.get("line_no", 1),
                smell_type=s.get("smell_type", "Unknown"),
                severity=s.get("severity", "INFO"),
                message=s.get("message", ""),
                suggestion=s.get("suggestion", ""),
            )
            for s in raw_smells
            if isinstance(s, dict)
        ]

    def put(self, file_path: Path, content: str | bytes, smells: List[CodeSmell]) -> None:
        if not self.enabled:
            return

        key = self._get_key(file_path)
        digest = self.compute_sha256(content)
        self._entries[key] = {
            "sha256": digest,
            "smells": [s.to_dict() for s in smells],
        }
        self._dirty = True

    def save(self) -> None:
        if not self.enabled or not self._dirty:
            return

        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": self.CACHE_SCHEMA_VERSION,
                "entries": self._entries,
            }
            tmp_file = self.cache_file.with_suffix(".tmp")
            tmp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_file.replace(self.cache_file)
            self._dirty = False
        except Exception:
            # Non-blocking on cache persistence failure
            pass

    def clear(self) -> None:
        self._entries.clear()
        self._dirty = False
        self.hits = 0
        self.misses = 0
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "total_cached_files": len(self._entries),
        }
