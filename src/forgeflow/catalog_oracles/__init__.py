"""Fail-closed loaders for immutable historical bundle oracles."""

import base64
import binascii
import hashlib
import json
import re
import zlib
from functools import lru_cache
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Dict, Any


ORACLE_SCHEMA_VERSION = 1
_VERSION_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_V048_PATHS = frozenset(
    {
        "docs/forgeflow/GOVERNANCE.md",
        "docs/forgeflow/spec/CHANGELOG.md",
        "docs/forgeflow/spec/FLOW_SPEC.md",
        "docs/forgeflow/spec/GATES_AND_LOOPS.md",
        "docs/forgeflow/templates/COMPLETION_REPORT.md",
        "docs/forgeflow/templates/DESIGN.md",
        "docs/forgeflow/templates/PRD.md",
        "docs/forgeflow/templates/QA_SIGNOFF.md",
        "docs/forgeflow/templates/ROADMAP.md",
    }
)
_EXPECTED_V050_PATHS = _EXPECTED_V048_PATHS
_EXPECTED_V060_PATHS = _EXPECTED_V048_PATHS | {
    "docs/forgeflow/templates/RELEASE_SIGNOFF.md",
    "docs/forgeflow/templates/RELEASE_NOTES.md",
}


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate oracle JSON key")
        result[key] = value
    return result


def _resource_name(version: str) -> str:
    if not isinstance(version, str) or not _VERSION_PATTERN.fullmatch(version):
        raise ValueError("invalid oracle version")
    return f"v{version}.json"


def _safe_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid oracle path")
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise ValueError("invalid oracle path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("invalid oracle path")
    normalized = path.as_posix()
    if normalized != value:
        raise ValueError("invalid oracle path")
    return normalized


def _decode_file(entry: Dict[str, Any]) -> tuple[str, str]:
    if set(entry) != {"path", "sha256", "encoding", "content"}:
        raise ValueError("invalid oracle file entry")
    path = _safe_path(entry["path"])
    digest = entry["sha256"]
    if not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest):
        raise ValueError("invalid oracle file digest")
    if entry["encoding"] != "utf-8+zlib+base64" or not isinstance(entry["content"], str):
        raise ValueError("invalid oracle file encoding")
    try:
        compressed = base64.b64decode(entry["content"].encode("ascii"), validate=True)
        content_bytes = zlib.decompress(compressed)
        content = content_bytes.decode("utf-8")
    except (UnicodeError, ValueError, binascii.Error, zlib.error) as exc:
        raise ValueError("invalid oracle file content") from exc

    if hashlib.sha256(content_bytes).hexdigest() != digest:
        raise ValueError(f"oracle digest mismatch: {path}")
    return path, content


_ORACLE_CACHE: Dict[str, Dict[str, str]] = {}


def _read_and_verify_oracle_bundle(version: str) -> Dict[str, str]:
    resource_name = _resource_name(version)
    expected_paths = {
        "0.4.8": _EXPECTED_V048_PATHS,
        "0.5.0": _EXPECTED_V050_PATHS,
        "0.6.0": _EXPECTED_V060_PATHS,
    }.get(version)
    if expected_paths is None:
        raise ValueError(f"unsupported oracle version: {version}")
    try:
        raw = resources.files(__name__).joinpath(resource_name).read_text(encoding="utf-8")
        document = json.loads(raw, object_pairs_hook=_strict_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid catalog oracle: {version}") from exc
    if not isinstance(document, dict) or set(document) != {"schema_version", "version", "files"}:
        raise ValueError("invalid catalog oracle schema")
    if document["schema_version"] != ORACLE_SCHEMA_VERSION or document["version"] != version:
        raise ValueError("catalog oracle version mismatch")
    entries = document["files"]
    if not isinstance(entries, list) or len(entries) != len(expected_paths):
        raise ValueError("invalid catalog oracle file list")
    bundle = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid catalog oracle file entry")
        path, content = _decode_file(entry)
        if path in bundle:
            raise ValueError("duplicate catalog oracle path")
        bundle[path] = content
    if set(bundle) != expected_paths:
        raise ValueError("catalog oracle path set mismatch")
    return bundle


def verify_oracle_integrity(version: str = "0.4.8") -> bool:
    """Validate the packaged oracle and return ``True`` only on exact success."""
    _read_and_verify_oracle_bundle(version)
    return True


def load_oracle(version: str = "0.4.8") -> Dict[Path, str]:
    """Load an immutable oracle only after complete integrity verification."""
    if version not in _ORACLE_CACHE:
        _ORACLE_CACHE[version] = _read_and_verify_oracle_bundle(version)
    bundle = _ORACLE_CACHE[version]
    return {Path(path): content for path, content in bundle.items()}


def clear_oracle_cache() -> None:
    _ORACLE_CACHE.clear()


__all__ = ["ORACLE_SCHEMA_VERSION", "load_oracle", "verify_oracle_integrity", "clear_oracle_cache"]
