"""Durable, host-neutral lifecycle control primitives.

The module deliberately has no knowledge of a CLI, a worker runtime, or Git.
It owns the small state machine that protects a lifecycle from stale writers and
from optimistic claims of completion.  Host integrations are implemented in
``adapter.py`` and ``supervisor.py``.
"""

from __future__ import annotations

import copy
import datetime as _datetime
from contextlib import contextmanager
import hashlib
import json
import os
import re
import secrets
import stat
import threading
import time
import unicodedata
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping


SCHEMA_VERSION = 2
MAX_HISTORY = 200
MAX_TEXT = 512
NO_PROGRESS_LIMIT = 5


class LifecycleError(RuntimeError):
    """Base exception for lifecycle violations."""


class ValidationError(LifecycleError, ValueError):
    """Raised when untrusted lifecycle input is malformed."""


class TransitionError(LifecycleError):
    """Raised when a state transition guard is not satisfied."""


class CASConflict(LifecycleError):
    """Raised when a stale revision, digest, or fencing epoch writes state."""


class AuthorityError(LifecycleError):
    """Raised when autonomous authority is missing or invalid."""


class Status(str, Enum):
    ACTIVE = "ACTIVE"
    WAITING_INTERNAL = "WAITING_INTERNAL"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"
    PACKAGE_REVIEW_PENDING = "PACKAGE_REVIEW_PENDING"
    PACKAGE_SEALED = "PACKAGE_SEALED"
    TARGET_REACHED = "TARGET_REACHED"
    COMPLETE = "COMPLETE"


class ContinuationPolicy(str, Enum):
    INTERACTIVE = "interactive"
    AUTONOMOUS = "autonomous"


class TargetCheckpoint(str, Enum):
    DESIGN_ONLY = "design-only"
    FULL = "full"
    CURRENT_STAGE = "current-stage"
    QA_SIGNOFF = "qa-signoff"


class OperationClass(str, Enum):
    READ_ONLY = "read_only"
    REPOSITORY_WRITE = "repository_write"
    LOCAL_COMMIT = "local_commit"
    EXTERNAL_WRITE = "external_write"
    DESTRUCTIVE = "destructive"


_ALLOWED_OPERATIONS = {
    OperationClass.READ_ONLY.value,
    OperationClass.REPOSITORY_WRITE.value,
    OperationClass.LOCAL_COMMIT.value,
}
_RELEASE_ID = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+-[a-z0-9][a-z0-9-]{2,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_HEX_SHA = re.compile(r"^[0-9a-f]{40}$")
_SECRET_PATTERNS = (
    re.compile(r'''(?i)(["']?(?:api[_-]?key|access[_-]?key|access[_-]?token|auth[_-]?token|token|password|passwd|secret|bearer|authorization|private[_-]?key|client[_-]?secret|credential)["']?)\s*:\s*(["'])(?:\\.|(?!\2).)*\2'''),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|token|password|passwd|secret|bearer)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)authorization\s*:\s*[^\r\n]+"),
    re.compile(r"(?i)(https?://)([^/\s:@]+):([^/@\s]+)@"),
)
_SENSITIVE_KEY_MARKERS = {
    "apikey", "accesskey", "accesstoken", "authtoken", "password", "passwd",
    "secret", "bearer", "credential", "privatekey", "clientsecret",
}


def canonical_json(value: Any) -> bytes:
    """Return the canonical JSON representation used by all digests."""

    try:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValidationError("value is not canonicalizable") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _bounded_text(value: Any, limit: int = MAX_TEXT) -> str:
    text = str(value).replace("\x00", "�")
    for pattern in _SECRET_PATTERNS:
        if pattern is _SECRET_PATTERNS[0]:
            text = pattern.sub(lambda match: f'{match.group(1)}:"[REDACTED]"', text)
        elif pattern.pattern.startswith("(?i)(https"):
            text = pattern.sub(r"\1[REDACTED]@", text)
        else:
            def redact(match: re.Match[str]) -> str:
                raw = match.group(0)
                separator = "=" if "=" in raw else ":"
                return raw.split(separator, 1)[0] + separator + "[REDACTED]"
            text = pattern.sub(redact, text)
    return text[:limit]


def safe_record(value: Any, *, allowed_keys: set[str] | None = None) -> Any:
    """Copy an untrusted value into a bounded, redacted JSON-safe record.

    Free-form execution output is intentionally not accepted by this function.
    Callers should pass summaries and references, never argv, environment,
    stdout, stderr, prompts, or tracebacks.
    """

    blocked = {
        "argv", "command", "env", "environment", "stdout", "stderr", "traceback",
        "prompt", "secret", "token", "password", "authorization", "remote_url",
    }
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _bounded_text(key, 80)
            key_marker = re.sub(r"[^a-z0-9]", "", key_text.lower())
            if key_text.lower() in blocked:
                continue
            if allowed_keys is not None and key_text not in allowed_keys:
                continue
            if key_marker in _SENSITIVE_KEY_MARKERS or key_marker.endswith(("secret", "token", "password")):
                output[key_text] = "[REDACTED]"
            else:
                output[key_text] = safe_record(item)
        return output
    if isinstance(value, (list, tuple)):
        return [safe_record(item) for item in list(value)[:32]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return _bounded_text(value) if isinstance(value, str) else value
    return _bounded_text(repr(value))


def safe_event(event: str, *, summary: str = "", duration_seconds: float | None = None,
               token_usage: int | None = None, evidence_ref: str | None = None) -> dict[str, Any]:
    """Build the allowlisted shape permitted in execution history."""

    result: dict[str, Any] = {"event": _bounded_text(event, 80), "summary": _bounded_text(summary)}
    if duration_seconds is not None:
        result["duration_seconds"] = max(0.0, float(duration_seconds))
    if token_usage is not None:
        result["token_usage"] = max(0, int(token_usage))
    if evidence_ref is not None:
        result["evidence_ref"] = _bounded_text(evidence_ref, 160)
    return result


def validate_release_id(release_id: str) -> str:
    normalized = unicodedata.normalize("NFC", str(release_id))
    if normalized != str(release_id) or not _RELEASE_ID.fullmatch(normalized):
        raise ValidationError("unsafe release id")
    return normalized


def validate_relative_path(path: str, root: str | os.PathLike[str] | None = None) -> str:
    raw = unicodedata.normalize("NFC", str(path))
    if not raw or raw != str(path) or "\x00" in raw or any(ord(char) < 32 for char in raw):
        raise ValidationError("unsafe path")
    candidate = Path(raw)
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        raise ValidationError("path must be relative and contained")
    if any(part in {"", "."} for part in candidate.parts):
        raise ValidationError("path contains an empty or dot component")
    normalized = candidate.as_posix()
    if root is not None:
        root_path = Path(root).resolve()
        current = root_path
        for part in candidate.parts:
            current = current / part
            if current.is_symlink():
                raise ValidationError("symlink path is not allowed")
        full = (root_path / normalized).resolve(strict=False)
        try:
            full.relative_to(root_path)
        except ValueError as exc:
            raise ValidationError("path escapes repository root") from exc
    return normalized


def _now_iso() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> float:
    try:
        text = value.replace("Z", "+00:00")
        return _datetime.datetime.fromisoformat(text).timestamp()
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValidationError("invalid timestamp") from exc


@dataclass(frozen=True)
class AutonomousPolicy:
    continuation_policy: str = ContinuationPolicy.INTERACTIVE.value
    target_checkpoint: str = TargetCheckpoint.FULL.value
    conditional_higher_tier: bool = False
    budget_override: Mapping[str, int | float] | None = None

    @classmethod
    def interactive(cls, target_checkpoint: str = TargetCheckpoint.FULL.value) -> "AutonomousPolicy":
        return cls(target_checkpoint=target_checkpoint)

    @classmethod
    def autonomous(cls, target_checkpoint: str = TargetCheckpoint.FULL.value,
                   *, conditional_higher_tier: bool = False,
                   budget_override: Mapping[str, int | float] | None = None) -> "AutonomousPolicy":
        return cls(ContinuationPolicy.AUTONOMOUS.value, target_checkpoint, conditional_higher_tier, budget_override)

    def validate(self) -> None:
        if self.continuation_policy not in {item.value for item in ContinuationPolicy}:
            raise ValidationError("unknown continuation policy")
        if self.target_checkpoint not in {item.value for item in TargetCheckpoint}:
            raise ValidationError("unknown target checkpoint")
        if not isinstance(self.conditional_higher_tier, bool):
            raise ValidationError("conditional_higher_tier must be boolean")
        if self.budget_override is not None:
            for key, value in self.budget_override.items():
                if key not in {"max_seconds", "max_tokens"} or not isinstance(value, (int, float)) or value < 0:
                    raise ValidationError("invalid budget override")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "continuation_policy": self.continuation_policy,
            "target_checkpoint": self.target_checkpoint,
            "conditional_higher_tier": self.conditional_higher_tier,
            "budget_override": dict(self.budget_override) if self.budget_override is not None else None,
        }


@dataclass(frozen=True)
class ActivationAttestation:
    lifecycle_id: str
    host_session_id: str
    adapter_id: str
    adapter_version: str
    user_intent_digest: str
    policy_digest: str
    nonce: str
    issued_at: str
    expires_at: str
    proof_digest: str
    verified: bool = False
    algorithm: str = "hmac-sha256"
    key_id: str = ""
    trust_anchor_id: str = ""
    signature: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "lifecycle_id": self.lifecycle_id,
            "host_session_id": self.host_session_id,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "user_intent_digest": self.user_intent_digest,
            "policy_digest": self.policy_digest,
            "nonce": self.nonce,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "proof_digest": self.proof_digest,
            "verified": self.verified,
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "trust_anchor_id": self.trust_anchor_id,
            "signature": self.signature,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ActivationAttestation":
        required = ("lifecycle_id", "host_session_id", "adapter_id", "adapter_version",
                    "user_intent_digest", "policy_digest", "nonce", "issued_at",
                    "expires_at", "proof_digest")
        if any(key not in value for key in required):
            raise ValidationError("incomplete activation attestation")
        return cls(**{key: value[key] for key in cls.__dataclass_fields__ if key in value})

    def validate(self, lifecycle_id: str, policy_digest: str, *, now: float | None = None,
                 require_verified: bool = True) -> None:
        validate_release_id(lifecycle_id)
        if self.lifecycle_id != lifecycle_id or self.policy_digest != policy_digest:
            raise AuthorityError("attestation binding mismatch")
        if not all(isinstance(item, str) and item for item in (
            self.host_session_id, self.adapter_id, self.adapter_version, self.user_intent_digest,
            self.policy_digest, self.nonce, self.proof_digest
        )):
            raise ValidationError("attestation contains empty identity field")
        if len(self.nonce) > 256 or not _SHA256.fullmatch(self.policy_digest) or not _SHA256.fullmatch(self.proof_digest):
            raise ValidationError("invalid attestation digest")
        if self.algorithm in {"", "none"} or not self.key_id or not self.trust_anchor_id or not self.signature:
            raise AuthorityError("attestation proof envelope is incomplete")
        current = time.time() if now is None else now
        if _parse_time(self.expires_at) <= current or _parse_time(self.issued_at) > current + 30:
            raise AuthorityError("attestation is expired or issued in the future")
        if require_verified and not self.verified:
            raise AuthorityError("attestation proof was not verified")


def _state_digest_payload(state: Mapping[str, Any]) -> dict[str, Any]:
    identity = state.get("identity", {})
    progress = state.get("progress", {})
    control = state.get("control", {})
    evidence = state.get("evidence", {})
    history = state.get("history", [])
    control_payload = {
        key: control.get(key) for key in ("operation_generation", "no_progress", "budget", "in_flight")
    }
    if control.get("loop_record") is not None:
        control_payload["loop_record"] = control["loop_record"]
    return {
        "identity": {key: identity.get(key) for key in ("release_id", "tier", "branch", "base_sha", "candidate_sha")},
        "progress": {key: progress.get(key) for key in ("stage", "status", "continuation_policy", "target_checkpoint", "current_action", "next_action")},
        "control": control_payload,
        "evidence": {
            "gate1": evidence.get("gate1"),
            "gate2": evidence.get("gate2"),
            "reviewers": evidence.get("reviewers", {}),
        },
        "history": history[-MAX_HISTORY:],
    }


def state_digest(state: Mapping[str, Any]) -> str:
    return digest(_state_digest_payload(state))


def _initial_state(release_id: str, *, tier: str = "Tier 3", branch: str = "",
                   base_sha: str = "", target_checkpoint: str = TargetCheckpoint.FULL.value) -> dict[str, Any]:
    validate_release_id(release_id)
    if target_checkpoint not in {item.value for item in TargetCheckpoint}:
        raise ValidationError("invalid target checkpoint")
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "identity": {
            "release_id": release_id, "tier": tier, "branch": branch,
            "base_sha": base_sha, "qa_sha": None, "candidate_sha": None,
        },
        "progress": {
            "stage": "stage-1", "status": Status.ACTIVE.value,
            "continuation_policy": ContinuationPolicy.INTERACTIVE.value,
            "target_checkpoint": target_checkpoint, "current_action": "plan",
            "next_action": "awaiting user-directed action",
        },
        "evidence": {
            "gate1": "PENDING", "gate2": "PENDING", "gate3": "PENDING",
            "reviewers": {}, "artifacts": [], "verification": {}, "strict_audit": {},
            "package_manifest_sha256": None, "package_seal": "PENDING",
        },
        "control": {
            "revision": 0, "fencing_epoch": 0, "operation_generation": 0,
            "no_progress": {
                "count": 0, "max": NO_PROGRESS_LIMIT, "stage_loop_fingerprint": None,
                "attempt_class": None, "last_increment_revision": None,
            },
            "budget": {"active_elapsed_seconds": 0.0, "token_usage": None,
                       "max_seconds": None, "max_tokens": None},
            "in_flight": None, "nonce_history": [],
            "loop_record": None,
        },
        "host": {"host_session_id": None, "adapter_id": None, "adapter_version": None,
                 "capabilities": {}, "attestation": None},
        "history": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    state["state_digest"] = state_digest(state)
    return state


def _validate_state(state: Mapping[str, Any]) -> None:
    if state.get("schema_version") not in {1, SCHEMA_VERSION}:
        raise ValidationError("unsupported lifecycle state schema")
    identity = state.get("identity")
    progress = state.get("progress")
    control = state.get("control")
    if not isinstance(identity, Mapping) or not isinstance(progress, Mapping) or not isinstance(control, Mapping):
        raise ValidationError("state sections are missing")
    validate_release_id(str(identity.get("release_id", "")))
    if progress.get("status") not in {item.value for item in Status}:
        raise ValidationError("unknown lifecycle status")
    if progress.get("continuation_policy") not in {item.value for item in ContinuationPolicy}:
        raise ValidationError("unknown lifecycle policy")
    if progress.get("target_checkpoint") not in {item.value for item in TargetCheckpoint}:
        raise ValidationError("unknown lifecycle target")
    for key in ("revision", "fencing_epoch", "operation_generation"):
        if not isinstance(control.get(key), int) or control[key] < 0:
            raise ValidationError("invalid lifecycle control counter")
    no_progress = control.get("no_progress")
    if not isinstance(no_progress, Mapping):
        raise ValidationError("invalid no-progress accounting")
    count = no_progress.get("count")
    if not isinstance(count, int) or count < 0 or count > NO_PROGRESS_LIMIT:
        raise ValidationError("no-progress limit exceeded")
    loop_record = control.get("loop_record")
    if loop_record is not None and not isinstance(loop_record, Mapping):
        raise ValidationError("invalid loop record")
    if not isinstance(state.get("history", []), list) or len(state.get("history", [])) > MAX_HISTORY:
        raise ValidationError("invalid lifecycle history")
    expected = state_digest(state)
    if state.get("state_digest") != expected:
        raise ValidationError("lifecycle state digest mismatch")


class LifecycleStore:
    """Atomic JSON state store with revision, digest, and fencing CAS checks."""

    _locks: dict[str, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, repository_root: str | os.PathLike[str], release_id: str):
        self.repository_root = Path(repository_root).resolve()
        self.release_id = validate_release_id(release_id)
        self.directory = self.repository_root / ".forgeflow" / "lifecycle"
        self.path = self.directory / f"{self.release_id}.json"
        self.lock_path = self.directory / f".{self.release_id}.lock"
        self._key = str(self.path)
        with self._locks_guard:
            self._locks.setdefault(self._key, threading.RLock())

    @property
    def lock(self) -> threading.RLock:
        return self._locks[self._key]

    def exists(self) -> bool:
        return self.path.exists()

    def _ensure_safe_directory(self) -> None:
        forgeflow_dir = self.repository_root / ".forgeflow"
        if forgeflow_dir.exists() and (forgeflow_dir.is_symlink() or not forgeflow_dir.is_dir()):
            raise ValidationError(".forgeflow must be a regular directory")
        if self.directory.exists() and (self.directory.is_symlink() or not self.directory.is_dir()):
            raise ValidationError("lifecycle directory must be a regular directory")
        self.directory.mkdir(parents=True, exist_ok=True)
        if forgeflow_dir.is_symlink() or self.directory.is_symlink():
            raise ValidationError("lifecycle parent cannot be a symlink")

    @contextmanager
    def _guard(self):
        """Combine an in-process lock with a cross-process kernel lock."""
        with self.lock:
            self._ensure_safe_directory()
            fd = -1
            try:
                fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
                try:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX)
                except (ImportError, OSError) as exc:
                    raise CASConflict("kernel lifecycle lock is unavailable") from exc
                yield
            finally:
                if fd >= 0:
                    try:
                        import fcntl
                        fcntl.flock(fd, fcntl.LOCK_UN)
                    finally:
                        os.close(fd)

    def load(self) -> dict[str, Any]:
        with self._guard():
            return self._load_unlocked()

    def _load_unlocked(self) -> dict[str, Any]:
        try:
            if self.path.is_symlink() or not self.path.is_file():
                raise ValidationError("lifecycle state is not a regular file")
            with self.path.open("rb") as handle:
                value = json.loads(handle.read().decode("utf-8"))
        except FileNotFoundError as exc:
            raise LifecycleError("lifecycle state does not exist") from exc
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("lifecycle state is unreadable") from exc
        if not isinstance(value, dict):
            raise ValidationError("lifecycle state must be an object")
        _validate_state(value)
        if value.get("identity", {}).get("release_id") != self.release_id:
            raise ValidationError("release id does not match state path")
        return copy.deepcopy(value)

    read = load

    def create(self, *, tier: str = "Tier 3", branch: str = "", base_sha: str = "",
               target_checkpoint: str = TargetCheckpoint.FULL.value) -> dict[str, Any]:
        state = _initial_state(self.release_id, tier=tier, branch=branch, base_sha=base_sha,
                               target_checkpoint=target_checkpoint)
        with self._guard():
            if self.path.exists():
                raise CASConflict("lifecycle already exists")
            self._write_atomic(state)
        return copy.deepcopy(state)

    def save(self, state: MutableMapping[str, Any], *, expected_revision: int | None = None,
             expected_digest: str | None = None, fencing_epoch: int | None = None) -> dict[str, Any]:
        with self._guard():
            current: dict[str, Any] | None = None
            if self.path.exists():
                current = self._load_unlocked()
                current_control = current["control"]
                if expected_revision is None or expected_revision != current_control["revision"]:
                    raise CASConflict("revision compare-and-swap failed")
                if expected_digest is not None and expected_digest != current["state_digest"]:
                    raise CASConflict("digest compare-and-swap failed")
                if fencing_epoch is None or fencing_epoch != current_control["fencing_epoch"]:
                    raise CASConflict("fencing compare-and-swap failed")
                next_revision = current_control["revision"] + 1
            else:
                if expected_revision is not None:
                    raise CASConflict("state appeared during create")
                next_revision = 0
            candidate = copy.deepcopy(dict(state))
            candidate.setdefault("identity", {})["release_id"] = self.release_id
            candidate.setdefault("control", {})["revision"] = next_revision
            if current is not None and candidate["control"].get("fencing_epoch") != current["control"]["fencing_epoch"]:
                raise CASConflict("candidate fencing epoch changed unexpectedly")
            candidate["control"]["revision"] = next_revision
            candidate["updated_at"] = _now_iso()
            candidate["state_digest"] = state_digest(candidate)
            _validate_state(candidate)
            self._write_atomic(candidate)
            return copy.deepcopy(candidate)

    def _write_atomic(self, state: Mapping[str, Any]) -> None:
        self._ensure_safe_directory()
        if self.path.is_symlink():
            raise ValidationError("state path cannot be a symlink")
        temporary = self.directory / f".{self.path.name}.{secrets.token_hex(8)}.tmp"
        payload = canonical_json(state)
        try:
            with temporary.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _policy_from(value: AutonomousPolicy | Mapping[str, Any] | None) -> AutonomousPolicy:
    if value is None:
        return AutonomousPolicy.interactive()
    if isinstance(value, AutonomousPolicy):
        value.validate()
        return value
    policy = AutonomousPolicy(**dict(value))
    policy.validate()
    return policy


class LifecycleController:
    """State transition and accounting facade over :class:`LifecycleStore`."""

    _transitions = {
        Status.ACTIVE.value: {Status.WAITING_INTERNAL.value, Status.PAUSED.value, Status.SUSPENDED.value,
                              Status.BLOCKED.value, Status.PACKAGE_REVIEW_PENDING.value,
                              Status.TARGET_REACHED.value, Status.COMPLETE.value},
        Status.WAITING_INTERNAL.value: {Status.ACTIVE.value, Status.PAUSED.value, Status.SUSPENDED.value,
                                        Status.BLOCKED.value},
        Status.PAUSED.value: {Status.ACTIVE.value},
        Status.SUSPENDED.value: {Status.ACTIVE.value},
        Status.BLOCKED.value: {Status.ACTIVE.value},
        Status.PACKAGE_REVIEW_PENDING.value: {Status.ACTIVE.value, Status.PAUSED.value,
                                               Status.SUSPENDED.value, Status.BLOCKED.value,
                                               Status.PACKAGE_SEALED.value,
                                               Status.COMPLETE.value},
        Status.PACKAGE_SEALED.value: {Status.ACTIVE.value, Status.PAUSED.value,
                                      Status.SUSPENDED.value, Status.BLOCKED.value,
                                      Status.PACKAGE_REVIEW_PENDING.value,
                                      Status.COMPLETE.value},
        Status.TARGET_REACHED.value: set(),
        Status.COMPLETE.value: set(),
    }

    def __init__(self, store: LifecycleStore):
        self.store = store

    @classmethod
    def start(cls, repository_root: str | os.PathLike[str], release_id: str, **kwargs: Any) -> "LifecycleController":
        store = LifecycleStore(repository_root, release_id)
        if not store.exists():
            store.create(**kwargs)
        return cls(store)

    @property
    def state(self) -> dict[str, Any]:
        return self.store.load()

    @property
    def status(self) -> Status:
        return Status(self.state["progress"]["status"])

    def _update(self, mutator: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        state = self.store.load()
        revision = state["control"]["revision"]
        current_digest = state["state_digest"]
        epoch = state["control"]["fencing_epoch"]
        candidate = copy.deepcopy(state)
        mutator(candidate)
        return self.store.save(candidate, expected_revision=revision, expected_digest=current_digest,
                               fencing_epoch=epoch)

    def set_fencing_epoch(self, new_epoch: int) -> dict[str, Any]:
        if not isinstance(new_epoch, int) or new_epoch <= self.state["control"]["fencing_epoch"]:
            raise CASConflict("fencing epoch must increase")
        def mutate(state: dict[str, Any]) -> None:
            state["control"]["fencing_epoch"] = new_epoch
            state["history"].append(safe_event("fence_issued", summary="controller epoch advanced"))
        return self._update(mutate)

    def update_evidence(self, **evidence: Any) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> None:
            state["evidence"].update(safe_record(evidence))
        return self._update(mutate)

    def activate(self, policy: AutonomousPolicy | Mapping[str, Any] | None = None,
                 attestation: ActivationAttestation | Mapping[str, Any] | None = None,
                 verifier: Callable[[ActivationAttestation], bool] | None = None,
                 *, now: float | None = None,
                 require_high_assurance: bool = False) -> dict[str, Any]:
        selected = _policy_from(policy)
        policy_digest = digest(selected.as_dict())
        parsed = None if attestation is None else (attestation if isinstance(attestation, ActivationAttestation)
                                                    else ActivationAttestation.from_mapping(attestation))
        current = self.state
        current_status = current["progress"]["status"]
        if selected.continuation_policy == ContinuationPolicy.AUTONOMOUS.value:
            is_high_assurance = require_high_assurance or os.environ.get("FORGEFLOW_REQUIRE_HIGH_ASSURANCE") == "true"
            if is_high_assurance:
                if parsed is None:
                    return self._block("autonomous_attestation_missing")
                try:
                    if verifier is None or not verifier(parsed):
                        raise AuthorityError("activation proof was not verified")
                    parsed = replace(parsed, verified=True)
                    parsed.validate(self.store.release_id, policy_digest, now=now, require_verified=True)
                    if parsed.nonce in current["control"].get("nonce_history", []):
                        raise AuthorityError("activation nonce was already consumed")
                except (LifecycleError, TypeError, ValueError):
                    return self._block("autonomous_attestation_invalid")
            elif parsed is not None:
                try:
                    if verifier is not None and not verifier(parsed):
                        raise AuthorityError("activation proof was not verified")
                    parsed = replace(parsed, verified=True)
                    parsed.validate(self.store.release_id, policy_digest, now=now, require_verified=True)
                    if parsed.nonce in current["control"].get("nonce_history", []):
                        raise AuthorityError("activation nonce was already consumed")
                except (LifecycleError, TypeError, ValueError):
                    return self._block("autonomous_attestation_invalid")
        elif parsed is not None:
            raise AuthorityError("interactive policy must not carry autonomous attestation")
        if current_status in {Status.PAUSED.value, Status.SUSPENDED.value, Status.BLOCKED.value} and parsed is None and (require_high_assurance or os.environ.get("FORGEFLOW_REQUIRE_HIGH_ASSURANCE") == "true"):
            raise AuthorityError("resume requires a fresh activation attestation")

        def mutate(state: dict[str, Any]) -> None:
            state["progress"]["continuation_policy"] = selected.continuation_policy
            state["progress"]["target_checkpoint"] = selected.target_checkpoint
            state["control"]["budget"].update(dict(selected.budget_override or {}))
            state["host"]["attestation"] = parsed.as_dict() if parsed is not None else None
            if parsed is not None:
                state["host"]["host_session_id"] = parsed.host_session_id
                state["host"]["adapter_id"] = parsed.adapter_id
                state["host"]["adapter_version"] = parsed.adapter_version
                state["control"]["nonce_history"].append(parsed.nonce)
            if selected.continuation_policy == ContinuationPolicy.AUTONOMOUS.value:
                loop_rec = dict(state["control"].get("loop_record") or {})
                loop_rec.setdefault("release_id", self.store.release_id)
                loop_rec.setdefault("continuation_policy", ContinuationPolicy.AUTONOMOUS.value)
                loop_rec.setdefault("stage", state["progress"].get("stage", "stage-1"))
                loop_rec.setdefault("candidate_sha", state["identity"].get("candidate_sha"))
                loop_rec.setdefault("attempt_count", 0)
                loop_rec.setdefault("no_progress_count", 0)
                loop_rec.setdefault("budget", NO_PROGRESS_LIMIT)
                loop_rec.setdefault("latest_verdict", "PENDING")
                loop_rec.setdefault("remediations", [])
                loop_rec.setdefault("failure_fingerprint", None)
                loop_rec.setdefault("next_action", state["progress"].get("next_action", "remediation"))
                loop_rec.setdefault("assigned_role", "implementer")
                loop_rec.setdefault("terminal_reason", None)
                state["control"]["loop_record"] = loop_rec
            state["history"].append(safe_event("policy_activated", summary=selected.continuation_policy))
        return self._update(mutate)

    def _block(self, reason: str) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> None:
            state["progress"]["status"] = Status.BLOCKED.value
            state["progress"]["next_action"] = "resolve authority or integrity blocker"
            state["history"].append(safe_event("blocked", summary=reason))
        return self._update(mutate)

    def resume(self, policy: AutonomousPolicy | Mapping[str, Any], attestation: ActivationAttestation | Mapping[str, Any],
               verifier: Callable[[ActivationAttestation], bool]) -> dict[str, Any]:
        activated = self.activate(policy, attestation, verifier)
        if activated["progress"]["status"] == Status.BLOCKED.value:
            raise AuthorityError("resume activation failed closed")
        return self.transition(Status.ACTIVE, reason="explicit resume", resume=True)

    def transition(self, target: Status | str, *, reason: str, resume: bool = False,
                   target_reached: bool = False) -> dict[str, Any]:
        target_value = target.value if isinstance(target, Status) else str(target)
        current = self.state
        source = current["progress"]["status"]
        if target_value not in self._transitions.get(source, set()):
            raise TransitionError(f"invalid transition {source} -> {target_value}")
        if target_value == Status.ACTIVE.value and source in {Status.PAUSED.value, Status.SUSPENDED.value, Status.BLOCKED.value} and not resume:
            raise TransitionError("resume transition requires explicit resume")
        if target_value == Status.WAITING_INTERNAL.value and current["control"].get("in_flight") is None:
            raise TransitionError("waiting state requires in-flight work")
        if target_value == Status.TARGET_REACHED.value:
            policy = current["progress"].get("target_checkpoint")
            if not target_reached and policy not in {TargetCheckpoint.DESIGN_ONLY.value, TargetCheckpoint.CURRENT_STAGE.value}:
                raise TransitionError("target checkpoint has not been reached")
        if target_value == Status.COMPLETE.value:
            ready, reasons = self.completion_ready()
            if not ready:
                raise TransitionError("completion guard failed: " + ", ".join(reasons))

        def mutate(state: dict[str, Any]) -> None:
            state["progress"]["status"] = target_value
            state["progress"]["next_action"] = "terminal" if target_value in {Status.TARGET_REACHED.value, Status.COMPLETE.value} else _bounded_text(reason)
            if target_value in {Status.PAUSED.value, Status.SUSPENDED.value}:
                state["control"]["operation_generation"] += 1
                if state["control"].get("in_flight") is not None:
                    state["control"]["in_flight"]["terminal_invalid"] = True
            state["history"].append(safe_event("transition", summary=f"{source}->{target_value}: {reason}"))
        return self._update(mutate)

    def begin_work(self, *, worker_id: str, invocation_id: str, attempt_id: str,
                   operation_generation: int | None = None) -> dict[str, Any]:
        current = self.state
        if current["progress"]["status"] not in {Status.ACTIVE.value, Status.WAITING_INTERNAL.value}:
            raise TransitionError("dispatch is forbidden in the current status")
        if current["control"].get("in_flight") is not None:
            raise TransitionError("work is already in flight")
        values = (worker_id, invocation_id, attempt_id)
        if not all(isinstance(value, str) and value for value in values):
            raise ValidationError("worker identity is required")
        def mutate(state: dict[str, Any]) -> None:
            if state["control"].get("in_flight") is not None:
                raise TransitionError("work is already in flight")
            state["control"]["in_flight"] = {
                "worker_id": worker_id, "invocation_id": invocation_id, "attempt_id": attempt_id,
                "operation_generation": state["control"]["operation_generation"] if operation_generation is None else operation_generation,
                "fencing_epoch": state["control"]["fencing_epoch"], "event_seq": 0,
            }
            state["progress"]["status"] = Status.WAITING_INTERNAL.value
        return self._update(mutate)

    def advance(self, *, stage: str | None = None, status: str | None = None,
                action: str | None = None, checkpoint: str | None = None,
                worker_id: str | None = None, invocation_id: str | None = None,
                attempt_id: str | None = None, candidate_sha: str | None = None) -> dict[str, Any]:
        current = self.state
        current_status = current["progress"]["status"]
        if current_status in {Status.BLOCKED.value, Status.PAUSED.value, Status.SUSPENDED.value,
                              Status.TARGET_REACHED.value, Status.COMPLETE.value}:
            raise TransitionError("advance is forbidden in the current status")
        if status not in {None, Status.ACTIVE.value, Status.WAITING_INTERNAL.value}:
            raise TransitionError("advance may only select ACTIVE or WAITING_INTERNAL")
        if worker_id is not None:
            if not invocation_id or not attempt_id:
                raise ValidationError("worker dispatch requires invocation and attempt identity")
            if status not in {None, Status.WAITING_INTERNAL.value}:
                raise TransitionError("worker dispatch must enter WAITING_INTERNAL")
            current = self.begin_work(
                worker_id=worker_id, invocation_id=invocation_id, attempt_id=attempt_id,
                operation_generation=current["control"]["operation_generation"],
            )
        elif status == Status.WAITING_INTERNAL.value:
            raise TransitionError("WAITING_INTERNAL requires an in-flight worker")
        elif status == Status.ACTIVE.value and current_status != Status.ACTIVE.value:
            raise TransitionError("ACTIVE transition requires worker completion")

        def mutate(state: dict[str, Any]) -> None:
            progress = state["progress"]
            if stage is not None:
                progress["stage"] = _bounded_text(stage, 80)
            if action is not None:
                progress["current_action"] = _bounded_text(action, 160)
                progress["next_action"] = _bounded_text(action, 160)
            if checkpoint is not None:
                progress["last_checkpoint"] = _bounded_text(checkpoint, 16)
            if candidate_sha is not None:
                if not _HEX_SHA.fullmatch(candidate_sha):
                    raise ValidationError("candidate SHA must be a 40-character lowercase hex SHA")
                state["identity"]["candidate_sha"] = candidate_sha
            if any(value is not None for value in (stage, action, checkpoint, candidate_sha)):
                state["control"]["operation_generation"] += 1

        updated = self._update(mutate) if any(
            value is not None for value in (stage, action, checkpoint, candidate_sha)
        ) else self.state
        if checkpoint == TargetCheckpoint.DESIGN_ONLY.value and updated["progress"]["status"] == Status.ACTIVE.value:
            return self.mark_target_reached()
        return updated

    def record_attempt(self, *, stage_loop_fingerprint: str, attempt_class: str,
                       progress: bool = False, remediation: bool = True,
                       duplicate: bool = False, elapsed_seconds: float = 0.0,
                       token_usage: int | None = None, failure: str = "",
                       next_action: str = "", evidence_ref: str | None = None) -> dict[str, Any]:
        if not isinstance(stage_loop_fingerprint, str) or not stage_loop_fingerprint:
            raise ValidationError("stage loop fingerprint is required")
        if self.status in {Status.BLOCKED, Status.PAUSED, Status.SUSPENDED,
                           Status.TARGET_REACHED, Status.COMPLETE}:
            raise TransitionError("attempt recording is forbidden in the current status")
        if elapsed_seconds < 0 or (token_usage is not None and token_usage < 0):
            raise ValidationError("accounting values cannot be negative")
        meaningful = remediation and not duplicate and attempt_class not in {"poll", "transient_retry", "duplicate_event"}
        def mutate(state: dict[str, Any]) -> None:
            if state["progress"]["status"] in {Status.BLOCKED.value, Status.PAUSED.value,
                                               Status.SUSPENDED.value, Status.TARGET_REACHED.value,
                                               Status.COMPLETE.value}:
                raise TransitionError("attempt recording is forbidden in the current status")
            control = state["control"]
            no_progress = control["no_progress"]
            budget = control["budget"]
            if state["progress"]["status"] in {Status.ACTIVE.value, Status.WAITING_INTERNAL.value}:
                budget["active_elapsed_seconds"] += float(elapsed_seconds)
            if token_usage is not None:
                budget["token_usage"] = int(budget.get("token_usage") or 0) + int(token_usage)
            if progress:
                no_progress.update(count=0, stage_loop_fingerprint=stage_loop_fingerprint,
                                   attempt_class=attempt_class, last_increment_revision=None)
            elif meaningful:
                if no_progress.get("stage_loop_fingerprint") != stage_loop_fingerprint:
                    no_progress["count"] = 0
                no_progress["stage_loop_fingerprint"] = stage_loop_fingerprint
                no_progress["attempt_class"] = attempt_class
                no_progress["count"] += 1
                no_progress["last_increment_revision"] = control["revision"] + 1
            if budget.get("max_seconds") is not None and budget["active_elapsed_seconds"] > budget["max_seconds"]:
                state["progress"]["status"] = Status.BLOCKED.value
                state["progress"]["next_action"] = "budget exceeded"
            elif budget.get("max_tokens") is not None and budget.get("token_usage") is not None and budget["token_usage"] > budget["max_tokens"]:
                state["progress"]["status"] = Status.BLOCKED.value
                state["progress"]["next_action"] = "budget exceeded"
            elif no_progress["count"] >= NO_PROGRESS_LIMIT:
                state["progress"]["status"] = Status.BLOCKED.value
                state["progress"]["next_action"] = "resolve repeated no-progress loop"
            if failure or next_action:
                state["history"].append(safe_event("attempt", summary=failure or next_action, duration_seconds=elapsed_seconds,
                                                    token_usage=token_usage, evidence_ref=evidence_ref))
            if len(state["history"]) > MAX_HISTORY:
                del state["history"][:-MAX_HISTORY]
        return self._update(mutate)

    def complete_work(self, *, event_seq: int, fencing_epoch: int, success: bool = True) -> dict[str, Any]:
        current = self.state
        inflight = current["control"].get("in_flight")
        if inflight is None:
            raise TransitionError("no in-flight work")
        if fencing_epoch != current["control"]["fencing_epoch"] or event_seq <= inflight.get("event_seq", 0):
            raise CASConflict("worker event fencing or sequence check failed")
        def mutate(state: dict[str, Any]) -> None:
            if success:
                state["control"]["in_flight"] = None
                state["progress"]["status"] = Status.ACTIVE.value
                state["control"]["no_progress"]["count"] = 0
            else:
                state["control"]["in_flight"]["event_seq"] = event_seq
            state["history"].append(safe_event("worker_result", summary="success" if success else "failure"))
        return self._update(mutate)

    def can_dispatch(self, operation: OperationClass | str) -> bool:
        value = operation.value if isinstance(operation, OperationClass) else str(operation)
        return self.status in {Status.ACTIVE, Status.WAITING_INTERNAL} and value in _ALLOWED_OPERATIONS

    def completion_ready(self) -> tuple[bool, list[str]]:
        state = self.state
        evidence = state.get("evidence", {})
        reasons: list[str] = []
        if evidence.get("gate1") != "APPROVED":
            reasons.append("gate1_not_approved")
        if evidence.get("gate2") != "APPROVED":
            reasons.append("gate2_not_approved")
        if evidence.get("gate3") != "APPROVED":
            reasons.append("gate3_not_approved")
        reviewers = evidence.get("reviewers", {})
        if reviewers and any(value != "APPROVED" for value in reviewers.values()):
            reasons.append("reviewer_not_approved")
        if not evidence.get("verification", {}).get("passed", False):
            reasons.append("verification_not_passed")
        if not state.get("identity", {}).get("qa_sha"):
            reasons.append("qa_sha_missing")
        if not state.get("identity", {}).get("candidate_sha"):
            reasons.append("candidate_missing")
        if not evidence.get("package_manifest_sha256") or evidence.get("package_seal") != "SEALED":
            reasons.append("package_not_sealed")
        if state["control"].get("in_flight") is not None:
            reasons.append("work_in_flight")
        if state["progress"]["status"] in {Status.BLOCKED.value, Status.SUSPENDED.value, Status.PAUSED.value}:
            reasons.append("status_not_completable")
        loop_record = state["control"].get("loop_record")
        if loop_record and isinstance(loop_record, dict):
            open_remediations = [r for r in loop_record.get("remediations", []) if r.get("status") == "OPEN"]
            if open_remediations or loop_record.get("latest_verdict") in {"REJECT", "FAIL"}:
                reasons.append("unresolved_remediation_active")
            if loop_record.get("terminal_reason") == "circuit-breaker":
                reasons.append("circuit_breaker_tripped")
        return not reasons, reasons

    def record_remediation(
        self,
        remediations: list[dict[str, Any]],
        *,
        verdict: str = "REJECT",
        failure_fingerprint: str | None = None,
        next_action: str = "remediation",
        assigned_role: str = "implementer",
    ) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> None:
            loop_rec = dict(state["control"].get("loop_record") or {})
            loop_rec["release_id"] = self.store.release_id
            loop_rec["continuation_policy"] = state["progress"].get("continuation_policy", ContinuationPolicy.INTERACTIVE.value)
            loop_rec["stage"] = state["progress"].get("stage", "stage-4")
            loop_rec["candidate_sha"] = state["identity"].get("candidate_sha")
            attempt = loop_rec.get("attempt_count", 0) + 1
            loop_rec["attempt_count"] = attempt
            prev_fp = loop_rec.get("failure_fingerprint")
            no_prog = loop_rec.get("no_progress_count", 0)
            if failure_fingerprint and prev_fp == failure_fingerprint:
                no_prog += 1
            else:
                no_prog = 1 if verdict in {"REJECT", "FAIL"} else 0
            loop_rec["no_progress_count"] = no_prog
            loop_rec["latest_verdict"] = verdict
            loop_rec["failure_fingerprint"] = failure_fingerprint
            loop_rec["assigned_role"] = assigned_role
            budget = loop_rec.get("budget", NO_PROGRESS_LIMIT)
            existing = {r.get("id"): r for r in loop_rec.get("remediations", [])}
            for rem in remediations:
                rid = rem.get("id") or f"REM-{len(existing) + 1:03d}"
                item = dict(rem)
                item["id"] = rid
                item.setdefault("status", "OPEN")
                existing[rid] = item
            loop_rec["remediations"] = list(existing.values())
            if no_prog >= budget:
                loop_rec["terminal_reason"] = "circuit-breaker"
                loop_rec["next_action"] = "circuit_breaker_tripped: authority decision required"
                state["progress"]["status"] = Status.BLOCKED.value
                state["progress"]["next_action"] = "circuit_breaker_tripped: authority decision required"
            else:
                loop_rec["next_action"] = next_action
                state["progress"]["next_action"] = next_action
            state["control"]["loop_record"] = loop_rec
            state["history"].append(safe_event("remediation_recorded", summary=f"verdict={verdict}, no_progress={no_prog}/{budget}"))
        return self._update(mutate)

    def resolve_remediation(
        self,
        remediation_id: str | None = None,
        *,
        candidate_sha: str | None = None,
        next_action: str = "verify",
    ) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> None:
            loop_rec = dict(state["control"].get("loop_record") or {})
            if candidate_sha is not None:
                if not _HEX_SHA.fullmatch(candidate_sha):
                    raise ValidationError("candidate SHA must be a 40-character lowercase hex SHA")
                state["identity"]["candidate_sha"] = candidate_sha
                loop_rec["candidate_sha"] = candidate_sha
            rems = loop_rec.get("remediations", [])
            for r in rems:
                if remediation_id is None or r.get("id") == remediation_id:
                    r["status"] = "RESOLVED"
            loop_rec["remediations"] = rems
            open_count = sum(1 for r in rems if r.get("status") == "OPEN")
            if open_count == 0:
                loop_rec["latest_verdict"] = "PASS"
                loop_rec["failure_fingerprint"] = None
                loop_rec["no_progress_count"] = 0
            loop_rec["next_action"] = next_action
            state["control"]["loop_record"] = loop_rec
            state["history"].append(safe_event("remediation_resolved", summary=f"resolved={remediation_id or 'all'}, remaining_open={open_count}"))
        return self._update(mutate)

    def get_loop_record(self) -> dict[str, Any] | None:
        return self.state.get("control", {}).get("loop_record")

    def mark_package_review_pending(self, *, qa_sha: str) -> dict[str, Any]:
        if not _HEX_SHA.fullmatch(qa_sha):
            raise ValidationError("QA SHA must be a 40-character lowercase hex SHA")
        state = self.state
        if state["progress"]["status"] == Status.PACKAGE_REVIEW_PENDING.value:
            if state["identity"].get("qa_sha") == qa_sha:
                return state
            def mutate(current: dict[str, Any]) -> None:
                current["identity"]["qa_sha"] = qa_sha
                current["progress"]["stage"] = "PACKAGE_REVIEW_PENDING"
                current["progress"]["last_checkpoint"] = "C4"
                current["progress"]["current_action"] = "await_release_package_review"
            return self._update(mutate)
        if state["evidence"].get("gate1") != "APPROVED" or state["evidence"].get("gate2") != "APPROVED":
            raise TransitionError("QA Sign-off is not approved")
        def mutate(current: dict[str, Any]) -> None:
            current["identity"]["qa_sha"] = qa_sha
            current["progress"]["stage"] = "PACKAGE_REVIEW_PENDING"
            current["progress"]["last_checkpoint"] = "C4"
            current["progress"]["current_action"] = "await_release_package_review"
        self._update(mutate)
        return self.transition(Status.PACKAGE_REVIEW_PENDING, reason="QA Sign-off approved; awaiting release package review")

    def seal_package(self, *, release_candidate_sha: str, package_manifest_sha256: str) -> dict[str, Any]:
        if not _HEX_SHA.fullmatch(release_candidate_sha) or not _SHA256.fullmatch(package_manifest_sha256):
            raise ValidationError("invalid package seal identity")
        state = self.state
        if state["progress"]["status"] == Status.PACKAGE_SEALED.value:
            if (state["identity"].get("candidate_sha") == release_candidate_sha
                    and state["evidence"].get("package_manifest_sha256") == package_manifest_sha256
                    and state["evidence"].get("package_seal") == "SEALED"):
                return state
            def mutate(current: dict[str, Any]) -> None:
                current["identity"]["candidate_sha"] = release_candidate_sha
                current["evidence"]["package_manifest_sha256"] = package_manifest_sha256
                current["evidence"]["package_seal"] = "SEALED"
                current["progress"]["stage"] = "PACKAGE_SEALED"
                current["progress"]["current_action"] = "run_strict_audit"
            return self._update(mutate)
        if self.state["evidence"].get("gate3") != "APPROVED":
            raise TransitionError("Release Sign-off is not approved")
        def mutate(current: dict[str, Any]) -> None:
            current["identity"]["candidate_sha"] = release_candidate_sha
            current["evidence"]["package_manifest_sha256"] = package_manifest_sha256
            current["evidence"]["package_seal"] = "SEALED"
            current["progress"]["stage"] = "PACKAGE_SEALED"
            current["progress"]["current_action"] = "run_strict_audit"
        self._update(mutate)
        return self.transition(Status.PACKAGE_SEALED, reason="Release Sign-off approved; package sealed")

    def unseal_package(self, *, reason: str = "package artifacts mutated after seal") -> dict[str, Any]:
        def mutate(current: dict[str, Any]) -> None:
            current["evidence"]["package_seal"] = "UNSEALED"
            current["evidence"]["gate3"] = None
            current["progress"]["stage"] = "PACKAGE_REVIEW_PENDING"
            current["progress"]["current_action"] = "await_release_package_review"
            current["progress"]["next_action"] = "re-review package and acquire Gate 3 sign-off"
        self._update(mutate)
        return self.transition(Status.PACKAGE_REVIEW_PENDING, reason=reason)

    def mark_target_reached(self) -> dict[str, Any]:
        return self.transition(Status.TARGET_REACHED, reason="target checkpoint reached", target_reached=True)
