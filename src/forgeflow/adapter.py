"""Host-neutral adapter contracts for lifecycle execution.

Only structured requests are accepted here.  A host may implement these
protocols with a native task runner, but the lifecycle core never treats a
capability probe or a cache entry as user authority.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import stat
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable

from .lifecycle import (
    ActivationAttestation,
    AutonomousPolicy,
    OperationClass,
    ValidationError,
    canonical_json,
    digest,
    safe_record,
    validate_relative_path,
)


class AdapterError(RuntimeError):
    """Raised when a host adapter cannot satisfy a lifecycle contract."""


@dataclass(frozen=True)
class Capabilities:
    can_wait: bool = False
    can_poll: bool = False
    can_cancel_write: bool = False
    can_record_usage: bool = False
    supported_operations: frozenset[str] = frozenset({OperationClass.READ_ONLY.value})

    def as_dict(self) -> dict[str, Any]:
        return {
            "can_wait": self.can_wait,
            "can_poll": self.can_poll,
            "can_cancel_write": self.can_cancel_write,
            "can_record_usage": self.can_record_usage,
            "supported_operations": sorted(self.supported_operations),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Capabilities":
        operations = frozenset(str(item) for item in value.get("supported_operations", []))
        unknown = operations.difference({item.value for item in OperationClass})
        if unknown:
            raise ValidationError("unknown capability operation")
        return cls(
            can_wait=bool(value.get("can_wait", False)),
            can_poll=bool(value.get("can_poll", False)),
            can_cancel_write=bool(value.get("can_cancel_write", False)),
            can_record_usage=bool(value.get("can_record_usage", False)),
            supported_operations=operations,
        )


@dataclass(frozen=True)
class WorkerRequest:
    """A non-shell worker request with an exact path allowlist."""

    operation_class: OperationClass | str
    planned_paths: tuple[str, ...] = ()
    baseline_digest: str = ""
    worker_id: str = ""
    invocation_id: str = ""
    attempt_id: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        operation = self.operation_class.value if isinstance(self.operation_class, OperationClass) else str(self.operation_class)
        if operation not in {item.value for item in OperationClass}:
            raise ValidationError("unknown operation class")
        object.__setattr__(self, "operation_class", operation)
        normalized: list[str] = []
        for path in self.planned_paths:
            normalized.append(validate_relative_path(path))
        if len(set(normalized)) != len(normalized):
            raise ValidationError("planned paths must be unique")
        object.__setattr__(self, "planned_paths", tuple(normalized))
        for value in (self.worker_id, self.invocation_id, self.attempt_id):
            if value and (not isinstance(value, str) or len(value) > 256 or "\x00" in value):
                raise ValidationError("invalid worker identity")
        if not isinstance(self.payload, Mapping):
            raise ValidationError("worker payload must be structured")
        if "shell" in self.payload or "command" in self.payload or "argv" in self.payload:
            raise ValidationError("shell and raw command payloads are forbidden")

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation_class": self.operation_class,
            "planned_paths": list(self.planned_paths),
            "baseline_digest": self.baseline_digest,
            "worker_id": self.worker_id,
            "invocation_id": self.invocation_id,
            "attempt_id": self.attempt_id,
            "payload": safe_record(self.payload),
        }


@dataclass(frozen=True)
class WorkerResult:
    worker_id: str
    invocation_id: str
    attempt_id: str
    event_seq: int
    fencing_epoch: int
    operation_generation: int
    success: bool
    summary: str = ""
    token_usage: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "invocation_id": self.invocation_id,
            "attempt_id": self.attempt_id,
            "event_seq": self.event_seq,
            "fencing_epoch": self.fencing_epoch,
            "operation_generation": self.operation_generation,
            "success": self.success,
            "summary": safe_record({"summary": self.summary}).get("summary", ""),
            "token_usage": self.token_usage,
        }


@runtime_checkable
class HostAdapter(Protocol):
    """Minimum transport boundary a supervisor may use."""

    adapter_id: str
    adapter_version: str

    def probe_capabilities(self) -> Capabilities: ...

    def dispatch_worker(self, request: WorkerRequest) -> str: ...

    def wait_worker(self, invocation_id: str, timeout_seconds: float) -> WorkerResult | None: ...

    def cancel_write_work(self, invocation_id: str) -> bool: ...

    def record_usage(self, invocation_id: str) -> int | None: ...

    def verify_activation_attestation(self, attestation: ActivationAttestation) -> bool: ...


def operation_allowed(operation: OperationClass | str, capabilities: Capabilities | None = None) -> bool:
    value = operation.value if isinstance(operation, OperationClass) else str(operation)
    if value not in {OperationClass.READ_ONLY.value, OperationClass.REPOSITORY_WRITE.value, OperationClass.LOCAL_COMMIT.value}:
        return False
    return capabilities is None or value in capabilities.supported_operations


def _proof_payload(attestation: ActivationAttestation) -> dict[str, Any]:
    value = attestation.as_dict()
    value.pop("signature", None)
    value.pop("verified", None)
    value.pop("proof_digest", None)
    return value


class HMACAttestationVerifier:
    """Small standard-library verifier for injected, pinned trust anchors."""

    algorithm = "hmac-sha256"

    def __init__(self, trust_anchors: Mapping[str, bytes | str], *, trust_anchor_id: str,
                 revoked_key_ids: Sequence[str] = ()):
        self._keys = {key: value.encode("utf-8") if isinstance(value, str) else bytes(value)
                      for key, value in trust_anchors.items()}
        self.trust_anchor_id = trust_anchor_id
        self.revoked_key_ids = frozenset(revoked_key_ids)

    def sign(self, attestation: ActivationAttestation, *, key_id: str) -> ActivationAttestation:
        if key_id not in self._keys or key_id in self.revoked_key_ids:
            raise AdapterError("unknown or revoked attestation key")
        envelope = ActivationAttestation(**{**attestation.as_dict(), "algorithm": self.algorithm,
                                            "key_id": key_id, "trust_anchor_id": self.trust_anchor_id,
                                            "signature": "", "proof_digest": ""})
        payload = canonical_json(_proof_payload(envelope))
        signature = base64.urlsafe_b64encode(hmac.new(self._keys[key_id], payload, hashlib.sha256).digest()).decode("ascii")
        proof_digest = hashlib.sha256(payload).hexdigest()
        return ActivationAttestation(**{**envelope.as_dict(), "signature": signature, "proof_digest": proof_digest})

    def __call__(self, attestation: ActivationAttestation) -> bool:
        if attestation.algorithm != self.algorithm or attestation.trust_anchor_id != self.trust_anchor_id:
            return False
        if not attestation.key_id or attestation.key_id in self.revoked_key_ids or attestation.key_id not in self._keys:
            return False
        payload = canonical_json(_proof_payload(attestation))
        if not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), attestation.proof_digest):
            return False
        try:
            expected = base64.b64decode(attestation.signature.encode("ascii"), altchars=b"-_", validate=True)
        except (ValueError, UnicodeError):
            return False
        return hmac.compare_digest(expected, hmac.new(self._keys[attestation.key_id], payload, hashlib.sha256).digest())

    verify = __call__


def make_attestation(*, lifecycle_id: str, host_session_id: str, adapter_id: str,
                     adapter_version: str, user_intent: str, policy: AutonomousPolicy,
                     nonce: str | None = None, issued_at: str, expires_at: str) -> ActivationAttestation:
    """Create an unsigned envelope; a configured verifier must sign it."""

    policy_digest = digest(policy.as_dict())
    intent_digest = hashlib.sha256(user_intent.encode("utf-8")).hexdigest()
    unsigned = ActivationAttestation(
        lifecycle_id=lifecycle_id, host_session_id=host_session_id, adapter_id=adapter_id,
        adapter_version=adapter_version, user_intent_digest=intent_digest,
        policy_digest=policy_digest, nonce=nonce or base64.urlsafe_b64encode(os.urandom(18)).decode("ascii"),
        issued_at=issued_at, expires_at=expires_at, proof_digest="0" * 64,
    )
    proof = hashlib.sha256(canonical_json(_proof_payload(unsigned))).hexdigest()
    return ActivationAttestation(**{**unsigned.as_dict(), "proof_digest": proof})


class CapabilityCache:
    """Validated, integrity-checked capability hint; never an authority source."""

    schema_version = 1

    def __init__(self, path: str | os.PathLike[str], *, host_id: str, adapter_id: str,
                 adapter_version: str, project_binding: str):
        self.path = Path(path)
        self.host_id = host_id
        self.adapter_id = adapter_id
        self.adapter_version = adapter_version
        self.project_binding = project_binding

    def _check_path(self) -> os.stat_result:
        if self.path.is_symlink():
            raise AdapterError("capability cache symlink is forbidden")
        self._check_path_ancestors()
        try:
            info = self.path.stat()
        except OSError as exc:
            raise AdapterError("capability cache is unavailable") from exc
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise AdapterError("capability cache ownership or permissions are unsafe")
        return info

    def load(self, *, now: float | None = None) -> Capabilities:
        self._check_path()
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdapterError("capability cache is unreadable") from exc
        if not isinstance(envelope, Mapping) or envelope.get("schema_version") != self.schema_version:
            raise AdapterError("unsupported capability cache schema")
        payload = envelope.get("payload")
        if not isinstance(payload, Mapping) or envelope.get("integrity") != digest(payload):
            raise AdapterError("capability cache integrity mismatch")
        if payload.get("host_id") != self.host_id or payload.get("adapter_id") != self.adapter_id or payload.get("adapter_version") != self.adapter_version or payload.get("project_binding") != self.project_binding:
            raise AdapterError("capability cache binding mismatch")
        current = time.time() if now is None else now
        try:
            if float(payload["expires_at"]) <= current:
                raise AdapterError("capability cache expired")
        except (KeyError, TypeError, ValueError) as exc:
            raise AdapterError("capability cache expiry is invalid") from exc
        return Capabilities.from_mapping(payload.get("capabilities", {}))

    def write(self, capabilities: Capabilities, *, issued_at: float | None = None,
              expires_at: float | None = None) -> None:
        issued = time.time() if issued_at is None else issued_at
        expires = issued + 300 if expires_at is None else expires_at
        payload = {
            "host_id": self.host_id, "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version, "project_binding": self.project_binding,
            "issued_at": issued, "expires_at": expires, "capabilities": capabilities.as_dict(),
        }
        envelope = {"schema_version": self.schema_version, "payload": payload, "integrity": digest(payload)}
        if self.path.exists() and (self.path.is_symlink() or not self.path.is_file()):
            raise AdapterError("capability cache path is not a regular file")
        if self.path.parent.exists() and not self.path.parent.is_dir():
            raise AdapterError("capability cache parent is not a directory")
        self._check_path_ancestors()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(self.path, flags, 0o600)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                fd = -1
                json.dump(envelope, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            if fd >= 0:
                os.close(fd)

    def _check_path_ancestors(self) -> None:
        current = self.path.absolute().parent
        trusted_system_aliases = {Path("/tmp"), Path("/var")}
        while True:
            if current.is_symlink() and current not in trusted_system_aliases:
                raise AdapterError("capability cache ancestor symlink is forbidden")
            if current.parent == current:
                break
            current = current.parent


class NullAdapter:
    """Explicit no-side-effect adapter useful as a safe default and fixture."""

    adapter_id = "null"
    adapter_version = "1"

    def probe_capabilities(self) -> Capabilities:
        return Capabilities(supported_operations=frozenset({OperationClass.READ_ONLY.value}))

    def dispatch_worker(self, request: WorkerRequest) -> str:
        raise AdapterError("null adapter does not dispatch work")

    def wait_worker(self, invocation_id: str, timeout_seconds: float) -> WorkerResult | None:
        return None

    def cancel_write_work(self, invocation_id: str) -> bool:
        return False

    def record_usage(self, invocation_id: str) -> int | None:
        return None

    def verify_activation_attestation(self, attestation: ActivationAttestation) -> bool:
        return False
