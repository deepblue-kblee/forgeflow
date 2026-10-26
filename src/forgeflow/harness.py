"""Harness Engine Orchestration for Gate Audits and Regression Verification."""

import base64
import hashlib
import hmac
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .runner import RuntimeTestRunner
from .adapter import HMACAttestationVerifier
from .lifecycle import (
    ActivationAttestation,
    AutonomousPolicy,
    LifecycleController as CoreLifecycleController,
    Status as CoreStatus,
)
from .scanner import HierarchicalRootScanner, ReleaseScanner
from .validator import (
    DocumentIntegrityValidator,
    MarkdownSectionParser,
    ReleaseCheckResult,
    TierRules,
)

try:  # v0.5.0 core is optional for legacy installations.
    from .lifecycle import LifecycleStore as CoreLifecycleStore
    from .lifecycle import ValidationError as CoreLifecycleValidationError
    from .lifecycle import AutonomousPolicy, digest as core_digest
    from .lifecycle import state_digest as core_state_digest
except ImportError:  # pragma: no cover - exercised only by legacy packages
    CoreLifecycleStore = None
    CoreLifecycleValidationError = ValueError
    AutonomousPolicy = None
    core_digest = None
    core_state_digest = None


class LifecycleError(ValueError):
    """A fail-closed lifecycle operation error."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class LegacyLifecycleStore:
    """Compatibility projection for pre-core CLI state files.

    The v0.5.0 core store is the canonical sectioned state source.  This
    projection remains only to read and safely migrate older flat CLI state;
    it has its own revision/digest/fencing record and never substitutes for
    the core controller when a sectioned state file is present.
    """

    SCHEMA_VERSION = 1
    STATUSES = {"ACTIVE", "WAITING_INTERNAL", "PAUSED", "SUSPENDED", "BLOCKED", "PACKAGE_REVIEW_PENDING", "PACKAGE_SEALED", "TARGET_REACHED", "COMPLETE"}
    POLICIES = {"interactive", "autonomous"}
    TARGETS = {"design-only", "full", "current-stage"}
    STAGES = {"STAGE_1", "GATE_1", "STAGE_3", "STAGE_4", "GATE_2", "PACKAGE_REVIEW_PENDING", "PACKAGE_SEALED", "COMPLETE"}
    CHECKPOINTS = {None, "C0", "D1", "C1", "C2", "C3", "C4"}
    _SAFE_CODE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")
    _SHA = re.compile(r"[0-9a-f]{40}")
    _DIGEST = re.compile(r"[0-9a-f]{64}")

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.state_dir = self.repo_root / ".forgeflow" / "lifecycle"

    @contextmanager
    def _kernel_lock(self):
        forgeflow_dir = self.repo_root / ".forgeflow"
        if forgeflow_dir.exists() and (forgeflow_dir.is_symlink() or not forgeflow_dir.is_dir()):
            raise LifecycleError("unsafe_state_path", "lifecycle parent is unsafe")
        if self.state_dir.exists() and (self.state_dir.is_symlink() or not self.state_dir.is_dir()):
            raise LifecycleError("unsafe_state_path", "lifecycle directory is unsafe")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.state_dir / ".cli-lifecycle.lock"
        fd = -1
        try:
            fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        except (ImportError, OSError) as exc:
            raise LifecycleError("lifecycle_lock_unavailable", "kernel lifecycle lock is unavailable") from exc
        finally:
            if fd >= 0:
                try:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)

    @classmethod
    def _state_digest(cls, state: Dict[str, object]) -> str:
        payload = dict(state)
        payload.pop("state_digest", None)
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @classmethod
    def validate_release_id(cls, release_id: str) -> str:
        if not isinstance(release_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", release_id):
            raise LifecycleError("invalid_release_id", "release ID must be a single safe path component")
        return release_id

    def path(self, release_id: str) -> Path:
        release_id = self.validate_release_id(release_id)
        path = self.state_dir / f"{release_id}.json"
        try:
            path.relative_to(self.repo_root)
        except ValueError as exc:
            raise LifecycleError("unsafe_state_path", "lifecycle state escapes repository root") from exc
        return path

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_time(value: object) -> datetime:
        if not isinstance(value, str) or not value:
            raise LifecycleError("malformed_attestation", "attestation timestamp is required")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LifecycleError("malformed_attestation", "attestation timestamp is invalid") from exc
        if parsed.tzinfo is None:
            raise LifecycleError("malformed_attestation", "attestation timestamp must include timezone")
        return parsed.astimezone(timezone.utc)

    @classmethod
    def validate_attestation(cls, attestation: object, release_id: str, policy: str, target: str = "full") -> Dict[str, object]:
        if policy != "autonomous":
            if attestation is not None:
                raise LifecycleError("unexpected_attestation", "interactive lifecycle cannot carry autonomous attestation")
            return {}
        if not isinstance(attestation, dict) or attestation.get("verified") is not True:
            raise LifecycleError("autonomous_activation_unverified", "autonomous lifecycle requires verified activation attestation")
        required = (
            "nonce", "expires_at", "issued_at", "lifecycle_id", "host_session_id",
            "adapter_id", "adapter_version", "user_intent_digest", "policy_digest",
            "algorithm", "key_id", "trust_anchor_id", "signature", "proof_digest",
        )
        if any(not isinstance(attestation.get(key), str) or not attestation[key] for key in required):
            raise LifecycleError("malformed_attestation", "activation attestation requires nonce and expires_at")
        if not cls._SAFE_CODE.fullmatch(attestation["nonce"]):
            raise LifecycleError("malformed_attestation", "activation nonce has unsafe characters")
        expires = cls._parse_time(attestation["expires_at"])
        if expires <= datetime.now(timezone.utc):
            raise LifecycleError("expired_attestation", "activation attestation has expired")
        if "lifecycle_id" in attestation and attestation["lifecycle_id"] != release_id:
            raise LifecycleError("attestation_binding_mismatch", "activation lifecycle binding does not match release ID")
        # Keep only the non-secret envelope fields.  Free-form adapter output
        # is never persisted in lifecycle state.
        allowed = {
            "verified", "nonce", "expires_at", "issued_at", "lifecycle_id",
            "host_session_id", "adapter_id", "adapter_version", "user_intent_digest",
            "policy_digest", "proof_digest", "algorithm", "key_id", "trust_anchor_id", "signature",
        }
        cleaned: Dict[str, object] = {}
        for key, value in attestation.items():
            if key not in allowed:
                raise LifecycleError("malformed_attestation", f"unsupported attestation field: {key}")
            if key.endswith("_digest") and (not isinstance(value, str) or not cls._DIGEST.fullmatch(value)):
                raise LifecycleError("malformed_attestation", f"invalid attestation digest: {key}")
            if key in {"issued_at"}:
                cls._parse_time(value)
            if key in {"lifecycle_id", "host_session_id", "adapter_id", "adapter_version", "algorithm", "key_id", "trust_anchor_id"} and not isinstance(value, str):
                raise LifecycleError("malformed_attestation", f"invalid attestation field: {key}")
            cleaned[key] = value
        cleaned["lifecycle_id"] = release_id
        if core_digest is None or AutonomousPolicy is None:
            raise LifecycleError("autonomous_activation_unverified", "autonomous policy verifier is unavailable")
        expected_policy_digest = core_digest(AutonomousPolicy.autonomous(target).as_dict())
        if cleaned.get("policy_digest") != expected_policy_digest:
            raise LifecycleError("attestation_binding_mismatch", "activation policy binding does not match target")
        expected_host = os.environ.get("FORGEFLOW_HOST_SESSION_ID")
        expected_adapter = os.environ.get("FORGEFLOW_ADAPTER_ID")
        expected_adapter_version = os.environ.get("FORGEFLOW_ADAPTER_VERSION")
        if not expected_host or not expected_adapter or not expected_adapter_version:
            raise LifecycleError("autonomous_activation_unverified", "autonomous host binding is unavailable")
        if (cleaned.get("host_session_id") != expected_host
                or cleaned.get("adapter_id") != expected_adapter
                or cleaned.get("adapter_version") != expected_adapter_version):
            raise LifecycleError("attestation_binding_mismatch", "activation host or adapter binding does not match")
        key_text = os.environ.get("FORGEFLOW_ATTESTATION_KEY")
        if not key_text or cleaned.get("algorithm") != "hmac-sha256":
            raise LifecycleError("autonomous_activation_unverified", "autonomous attestation verifier is unavailable")
        signature = cleaned.get("signature")
        proof_digest = cleaned.get("proof_digest")
        if not isinstance(signature, str) or not isinstance(proof_digest, str) or not cls._DIGEST.fullmatch(proof_digest):
            raise LifecycleError("autonomous_activation_unverified", "autonomous attestation proof is incomplete")
        proof_payload = dict(cleaned)
        proof_payload.pop("signature", None)
        proof_payload.pop("verified", None)
        proof_payload.pop("proof_digest", None)
        canonical = (json.dumps(proof_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if not hmac.compare_digest(hashlib.sha256(canonical).hexdigest(), proof_digest):
            raise LifecycleError("autonomous_activation_unverified", "autonomous attestation proof digest is invalid")
        try:
            expected = base64.b64decode(signature.encode("ascii"), altchars=b"-_", validate=True)
        except (ValueError, UnicodeError) as exc:
            raise LifecycleError("autonomous_activation_unverified", "autonomous attestation signature is invalid") from exc
        if not hmac.compare_digest(expected, hmac.new(key_text.encode("utf-8"), canonical, hashlib.sha256).digest()):
            raise LifecycleError("autonomous_activation_unverified", "autonomous attestation signature is invalid")
        return cleaned

    @staticmethod
    def _git_sha(repo_root: Path, ref: str = "HEAD") -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", ref],
                capture_output=True, text=True, check=False,
            )
        except OSError:
            return None
        value = result.stdout.strip()
        return value if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None

    def exists(self, release_id: str) -> bool:
        path = self.path(release_id)
        return path.exists() and not path.is_symlink()

    def load(self, release_id: str) -> Dict[str, object]:
        path = self.path(release_id)
        if path.is_symlink() or not path.is_file():
            raise LifecycleError("lifecycle_state_missing", "lifecycle state does not exist")
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LifecycleError("lifecycle_state_malformed", "lifecycle state is not valid JSON") from exc
        # A state produced by the v0.5.0 lifecycle core uses sectioned
        # identity/progress/control records.  Let that API perform its own
        # digest and CAS validation instead of interpreting it as the small
        # CLI compatibility schema below.
        if isinstance(value, dict) and {"identity", "progress", "control"}.issubset(value):
            if CoreLifecycleStore is None:
                raise LifecycleError("lifecycle_state_malformed", "lifecycle core is unavailable")
            try:
                return CoreLifecycleStore(self.repo_root, release_id).load()
            except Exception as exc:
                raise LifecycleError("lifecycle_state_malformed", "lifecycle core rejected state") from exc
        self.validate(value, release_id)
        return value

    @classmethod
    def validate(cls, state: object, release_id: str) -> None:
        if not isinstance(state, dict):
            raise LifecycleError("lifecycle_state_malformed", "lifecycle state must be an object")
        required = {
            "schema_version", "release_id", "tier", "stage", "status", "continuation_policy",
            "target_checkpoint", "target", "current_action", "current_worker", "no_progress",
            "budget", "last_checkpoint", "candidate_sha", "base_sha", "activation_attestation",
            "attempts", "history", "next_action", "operation_generation", "updated_at",
            "revision", "fencing_epoch", "state_digest",
        }
        if set(state) != required:
            raise LifecycleError("lifecycle_state_malformed", "lifecycle state fields do not match schema")
        if state["schema_version"] != cls.SCHEMA_VERSION or state["release_id"] != release_id:
            raise LifecycleError("lifecycle_state_malformed", "schema or release binding is invalid")
        if state["tier"] not in {1, 2, 3} or state["stage"] not in cls.STAGES or state["status"] not in cls.STATUSES:
            raise LifecycleError("lifecycle_state_malformed", "tier, stage, or status is invalid")
        if state["continuation_policy"] not in cls.POLICIES or state["target"] not in cls.TARGETS:
            raise LifecycleError("lifecycle_state_malformed", "policy or target is invalid")
        if state["target_checkpoint"] not in cls.CHECKPOINTS or state["last_checkpoint"] not in cls.CHECKPOINTS:
            raise LifecycleError("lifecycle_state_malformed", "checkpoint is invalid")
        for key in ("base_sha", "candidate_sha"):
            if state[key] is not None and (not isinstance(state[key], str) or not cls._SHA.fullmatch(state[key])):
                raise LifecycleError("lifecycle_state_malformed", f"{key} is invalid")
        if not isinstance(state["current_action"], str) or len(state["current_action"]) > 128:
            raise LifecycleError("lifecycle_state_malformed", "current action is invalid")
        if state["current_worker"] is not None and (not isinstance(state["current_worker"], str) or not cls._SAFE_CODE.fullmatch(state["current_worker"])):
            raise LifecycleError("lifecycle_state_malformed", "current worker is invalid")
        no_progress = state["no_progress"]
        if not isinstance(no_progress, dict) or set(no_progress) != {"count", "max", "fingerprint"}:
            raise LifecycleError("lifecycle_state_malformed", "no-progress record is invalid")
        if not isinstance(no_progress["count"], int) or not isinstance(no_progress["max"], int) or no_progress["max"] != 5 or not 0 <= no_progress["count"] <= 5:
            raise LifecycleError("lifecycle_state_malformed", "no-progress limits are invalid")
        if not isinstance(no_progress["fingerprint"], str) or not cls._SAFE_CODE.fullmatch(no_progress["fingerprint"]):
            raise LifecycleError("lifecycle_state_malformed", "no-progress fingerprint is invalid")
        budget = state["budget"]
        if not isinstance(budget, dict) or set(budget) != {"limit", "used"} or (budget["limit"] is not None and (not isinstance(budget["limit"], int) or budget["limit"] < 0)) or not isinstance(budget["used"], int) or budget["used"] < 0:
            raise LifecycleError("lifecycle_state_malformed", "budget record is invalid")
        if not isinstance(state["attempts"], list) or not isinstance(state["history"], list) or len(state["history"]) > 1000:
            raise LifecycleError("lifecycle_state_malformed", "history is invalid")
        if state["next_action"] is not None and (not isinstance(state["next_action"], str) or len(state["next_action"]) > 128):
            raise LifecycleError("lifecycle_state_malformed", "next action is invalid")
        if not isinstance(state["operation_generation"], int) or state["operation_generation"] < 0:
            raise LifecycleError("lifecycle_state_malformed", "operation generation is invalid")
        if not isinstance(state["revision"], int) or state["revision"] < 0:
            raise LifecycleError("lifecycle_state_malformed", "revision is invalid")
        if not isinstance(state["fencing_epoch"], int) or state["fencing_epoch"] < 0:
            raise LifecycleError("lifecycle_state_malformed", "fencing epoch is invalid")
        if not isinstance(state["state_digest"], str) or not cls._DIGEST.fullmatch(state["state_digest"]):
            raise LifecycleError("lifecycle_state_malformed", "state digest is invalid")
        if state["state_digest"] != cls._state_digest(state):
            raise LifecycleError("lifecycle_state_malformed", "state digest does not match state")
        cls._parse_time(state["updated_at"])
        cls.validate_attestation(state["activation_attestation"], release_id, state["continuation_policy"], str(state["target"]))
        if state["status"] == "TARGET_REACHED" and state["target"] != "design-only":
            raise LifecycleError("lifecycle_state_malformed", "only design-only may reach TARGET_REACHED")
        if state["status"] == "COMPLETE" and state["last_checkpoint"] != "C4":
            raise LifecycleError("lifecycle_state_malformed", "complete state requires C4 checkpoint")

    def save(self, state: Dict[str, object]) -> None:
        with self._kernel_lock():
            release_id = str(state.get("release_id", ""))
            path = self.path(release_id)
            if path.is_symlink():
                raise LifecycleError("unsafe_state_path", "lifecycle state file is a symlink")
            if path.exists():
                current = self.load(release_id)
                if current.get("revision") != state.get("revision") or current.get("state_digest") != state.get("state_digest"):
                    raise LifecycleError("lifecycle_state_cas_conflict", "lifecycle state revision or digest is stale")
                state = dict(state)
                state["revision"] = int(state["revision"]) + 1
                state["fencing_epoch"] = current["fencing_epoch"]
                state["updated_at"] = self._now()
                state["state_digest"] = self._state_digest(state)
            self.validate(state, release_id)
            payload = json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(self.state_dir), text=True)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, path)
                dir_fd = os.open(self.state_dir, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except OSError as exc:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass
                raise LifecycleError("lifecycle_state_write_failed", "could not persist lifecycle state") from exc

    def create(self, release_id: str, tier: int, policy: str = "interactive", target: str = "full", attestation: object = None) -> Dict[str, object]:
        self.validate_release_id(release_id)
        if self.exists(release_id):
            raise LifecycleError("lifecycle_state_exists", "lifecycle state already exists")
        if policy not in self.POLICIES or target not in self.TARGETS:
            raise LifecycleError("invalid_lifecycle_policy", "policy or target is invalid")
        activation = self.validate_attestation(attestation, release_id, policy, target)
        base = self._git_sha(self.repo_root)
        now = self._now()
        state: Dict[str, object] = {
            "schema_version": self.SCHEMA_VERSION,
            "release_id": release_id,
            "tier": tier,
            "stage": "STAGE_1",
            "status": "ACTIVE",
            "continuation_policy": policy,
            "target_checkpoint": "D1" if target == "design-only" else "C4",
            "target": target,
            "current_action": "plan",
            "current_worker": None,
            "no_progress": {"count": 0, "max": 5, "fingerprint": "STAGE_1:plan"},
            "budget": {"limit": None, "used": 0},
            "last_checkpoint": None,
            "candidate_sha": base,
            "base_sha": base,
            "activation_attestation": activation or None,
            "attempts": [],
            "history": [{"event": "start", "at": now, "status": "ACTIVE"}],
            "next_action": "complete Gate 1 and create C0",
            "operation_generation": 0,
            "revision": 0,
            "fencing_epoch": 0,
            "updated_at": now,
        }
        state["state_digest"] = self._state_digest(state)
        self.save(state)
        return state

    def update(self, state: Dict[str, object], event: str) -> None:
        state["history"].append({"event": event, "at": self._now(), "status": state["status"]})
        state["history"] = state["history"][-1000:]
        state["updated_at"] = self._now()
        self.save(state)


class HarnessEngine:
    """Orchestrates audit checks across release directories."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = (repo_root or HierarchicalRootScanner.find_root()).resolve()

    def _release_dir(self, release_id: str) -> Path:
        """Resolve release directory using ReleaseScanner, falling back to legacy docs/releases."""
        found = ReleaseScanner.find_release_path(self.repo_root, release_id)
        if found:
            return found
        configured = ReleaseScanner._read_configured_tasks_dir(self.repo_root)
        if configured:
            for sub in ("in-progress", "completed", "backlog", ""):
                p = self.repo_root / configured / sub / release_id if sub else self.repo_root / configured / release_id
                if p.exists() and p.is_dir():
                    return p
            return self.repo_root / configured / "in-progress" / release_id
        if (self.repo_root / "tasks").exists() and (self.repo_root / "tasks").is_dir():
            for sub in ("in-progress", "completed", "backlog", ""):
                p = self.repo_root / "tasks" / sub / release_id if sub else self.repo_root / "tasks" / release_id
                if p.exists() and p.is_dir():
                    return p
            return self.repo_root / "tasks" / "in-progress" / release_id
        return self.repo_root / "docs" / "releases" / release_id

    def _release_rel_path(self, release_id: str) -> str:
        full = self._release_dir(release_id)
        try:
            return str(full.relative_to(self.repo_root))
        except ValueError:
            return f"docs/releases/{release_id}"

    def check_release(
        self,
        release_path: Path,
        strict: bool = False,
        explicit_python: Optional[str] = None,
    ) -> ReleaseCheckResult:
        validator = DocumentIntegrityValidator(release_path)
        rel_id = release_path.name
        res = ReleaseCheckResult(release_id=rel_id, path=str(release_path))

        # Check if hybrid release package
        spec_file = release_path / "spec.md"
        gate1_file = release_path / "GATE1_REVIEW.md"
        prd_file = release_path / "PRD.md"
        change_note = release_path / "CHANGE_NOTE.md"
        is_hybrid = spec_file.exists() or gate1_file.exists() or (release_path.parent.parent / ".specify").is_dir()
        is_completed = "completed" in str(release_path)

        if is_hybrid:
            if spec_file.exists():
                try:
                    res.tier = MarkdownSectionParser.extract_tier(spec_file.read_text(encoding="utf-8"))
                except Exception:
                    res.tier = None
            if not res.tier and gate1_file.exists():
                try:
                    res.tier = MarkdownSectionParser.extract_tier(gate1_file.read_text(encoding="utf-8"))
                except Exception:
                    res.tier = None
            if not res.tier:
                res.tier = 2
            required_docs = TierRules.get_required_docs(res.tier, is_hybrid=True, is_completed=is_completed)
        elif change_note.exists() and not prd_file.exists():
            try:
                res.tier = MarkdownSectionParser.extract_tier(
                    change_note.read_text(encoding="utf-8")
                )
            except Exception:
                res.tier = None
            if res.tier != 1:
                res.tier = 2
            required_docs = ["CHANGE_NOTE.md"] if res.tier == 1 else TierRules.get_required_docs(res.tier)
        elif prd_file.exists():
            try:
                content = prd_file.read_text(encoding="utf-8")
                res.tier = MarkdownSectionParser.extract_tier(content)
            except Exception:
                res.tier = 2
            required_docs = TierRules.get_required_docs(res.tier)
        else:
            res.tier = 2
            required_docs = TierRules.get_required_docs(res.tier)
        doc_passed_count = 0

        for doc_name in required_docs:
            d_stat = validator.validate_file(doc_name)
            res.documents[doc_name] = {
                "exists": d_stat.exists,
                "passed": d_stat.passed,
                "details": d_stat.details,
            }
            if d_stat.passed:
                doc_passed_count += 1
            if d_stat.errors:
                res.errors.extend(d_stat.errors)
            if d_stat.warnings:
                res.warnings.extend(d_stat.warnings)

        docs_all_ok = doc_passed_count == len(required_docs)

        # 2. Strict mode: run regression test suite and module bloat check
        if strict:
            test_res = RuntimeTestRunner.run_tests(
                repo_root=self.repo_root, explicit_python=explicit_python
            )
            res.tests = test_res
            if not test_res.get("passed"):
                res.errors.append("회귀 테스트 스위트가 100% 통과하지 못했습니다.")
                res.passed = False
                return res

            bloat_errors = self._check_module_bloat_strict(release_path)
            if bloat_errors:
                res.errors.extend(bloat_errors)
                res.passed = False
                return res

        res.passed = docs_all_ok and (not strict or res.tests.get("passed", True))
        return res

    def _check_module_bloat_strict(self, release_path: Path) -> List[str]:
        """Detect modules > 800 LOC in changed files and enforce Architecture Exception justification."""
        errors = []
        try:
            diff_cmd = subprocess.run(
                ["git", "-C", str(self.repo_root), "diff", "--name-only", "-z", "HEAD"],
                capture_output=True, text=True, check=False,
            )
            changed = set()
            if diff_cmd.returncode == 0:
                for f in diff_cmd.stdout.split("\0"):
                    if f.strip().endswith(".py"):
                        changed.add(f.strip())
            status_cmd = subprocess.run(
                ["git", "-C", str(self.repo_root), "status", "--porcelain", "-z"],
                capture_output=True, text=True, check=False,
            )
            if status_cmd.returncode == 0:
                for item in status_cmd.stdout.split("\0"):
                    if len(item) > 3 and item[3:].strip().endswith(".py"):
                        changed.add(item[3:].strip())
        except Exception:
            return []

        doc_contents = []
        for doc_name in ("DESIGN.md", "QA_SIGNOFF.md", "PRD.md"):
            p = release_path / doc_name
            if p.exists():
                try:
                    doc_contents.append(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        combined_docs = "\n".join(doc_contents)
        has_exception_header = bool(
            re.search(
                r"(?:Architecture Exception|LOC Exception|모듈\s*비대화\s*예외|God Module Exception)",
                combined_docs,
                re.IGNORECASE,
            )
        )

        for rel_f in sorted(changed):
            full_p = self.repo_root / rel_f
            if full_p.exists() and full_p.is_file():
                try:
                    lines = full_p.read_text(encoding="utf-8").splitlines()
                    loc = len(lines)
                    if loc > 800:
                        file_name = full_p.name
                        module_exempted = has_exception_header and (
                            file_name in combined_docs or rel_f in combined_docs
                        )
                        if not module_exempted:
                            errors.append(
                                f"모듈 비대화 임계치 초과(CRITICAL): '{rel_f}' ({loc}줄 > 800줄). "
                                f"DESIGN.md 또는 QA_SIGNOFF.md에 'Architecture Exception' 섹션 및 승인 사유 기록이 필수입니다."
                            )
                except Exception:
                    pass
        return errors

    def check_all_releases(
        self, strict: bool = False, explicit_python: Optional[str] = None
    ) -> List[ReleaseCheckResult]:
        releases = ReleaseScanner.get_all_releases(self.repo_root)
        if not releases:
            return []

        results = []
        # In strict mode, run tests once for the suite
        suite_tests_passed = True
        suite_test_data = {}
        if strict:
            suite_test_data = RuntimeTestRunner.run_tests(
                repo_root=self.repo_root, explicit_python=explicit_python
            )
            suite_tests_passed = suite_test_data.get("passed", False)

        # Detect changed paths in working tree and recent commits
        changed_paths: set[str] = set()
        try:
            status = subprocess.run(
                ["git", "-C", str(self.repo_root), "status", "--porcelain", "-z"],
                capture_output=True, text=True, check=False
            )
            if status.returncode == 0:
                for item in status.stdout.split("\0"):
                    if len(item) > 3:
                        changed_paths.add(item[3:].strip())
            diff = subprocess.run(
                ["git", "-C", str(self.repo_root), "diff", "--name-only", "-z", "HEAD"],
                capture_output=True, text=True, check=False
            )
            if diff.returncode == 0:
                for item in diff.stdout.split("\0"):
                    if item.strip():
                        changed_paths.add(item.strip())
        except Exception:
            pass

        for rel_p in releases:
            rel_str = str(rel_p.relative_to(self.repo_root))
            is_changed = any(cp.startswith(rel_str + "/") or cp == rel_str for cp in changed_paths)
            change_note = rel_p / "CHANGE_NOTE.md"
            if change_note.exists():
                is_completed = True
                has_all_required = True
                doc_keys = ["CHANGE_NOTE.md"]
            else:
                has_all_required = all((rel_p / name).exists() for name in ("PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md"))
                is_completed = (rel_p / "COMPLETION_REPORT.md").exists()
                doc_keys = ["PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md"]

            if is_completed and has_all_required and not is_changed:
                # Incremental audit: completed archived release with no changes skips parsing
                r = ReleaseCheckResult(
                    release_id=rel_p.name,
                    path=str(rel_p),
                    tier=1 if change_note.exists() else 3,
                    passed=True,
                    archived=True,
                )
                r.documents = {
                    name: {"exists": True, "passed": True, "details": {}}
                    for name in doc_keys
                }
            else:
                r = self.check_release(rel_p, strict=False)

            if strict:
                r.tests = suite_test_data
                if not suite_tests_passed:
                    r.errors.append("회귀 테스트 스위트가 100% 통과하지 못했습니다.")
                    r.passed = False
            results.append(r)

        return results

    def check_latest_release(
        self, strict: bool = False, explicit_python: Optional[str] = None
    ) -> Optional[ReleaseCheckResult]:
        latest = ReleaseScanner.get_latest_release(self.repo_root)
        if not latest:
            return None
        return self.check_release(latest, strict=strict, explicit_python=explicit_python)

    def check_lifecycle_evidence(
        self,
        release_id: str,
        strict: bool = False,
        explicit_python: Optional[str] = None,
        require_terminal_state: bool = True,
    ) -> Dict[str, object]:
        """Read release artifacts and report Gate-2 evidence completeness.

        This intentionally reads only durable release artifacts.  It does not
        load an agent task record, create work, or infer an orchestrator's
        runtime state.
        """
        release_path = self._release_dir(release_id)
        unmet: List[str] = []
        try:
            LegacyLifecycleStore.validate_release_id(release_id)
        except LifecycleError:
            return self._lifecycle_result(release_id, ["invalid_release_id"], None)
        if not self._safe_release_directory(release_path):
            return self._lifecycle_result(release_id, ["release_artifacts_missing"], None)

        release_check = self.check_release(release_path, strict=False)
        for name, document in release_check.documents.items():
            if not document["passed"]:
                unmet.append(f"artifact_incomplete:{name}")

        qa_path = release_path / "QA_SIGNOFF.md"
        qa_text = self._read_regular_text(qa_path)
        if qa_text is None:
            unmet.append("qa_signoff_unreadable")
            return self._lifecycle_result(release_id, unmet, None)
        evidence_version = 1
        try:
            if "## ForgeFlow Evidence v2" in qa_text:
                evidence_version = 2
                evidence = self._parse_evidence_v2(qa_text)
                self._validate_evidence_v2(release_id, qa_text, evidence)
            else:
                evidence = self._parse_evidence_block(qa_text)
                self._validate_evidence(release_id, release_path, qa_text, evidence)
        except ValueError as exc:
            # Evidence is untrusted repository content.  Do not attempt to
            # recover a partial approval from prose when its fixed schema is
            # malformed or incomplete.
            unmet.append(f"evidence_malformed:{exc}")
            evidence = None

        if evidence is not None and evidence_version == 1:
            candidate = evidence["Candidate-SHA"]
            if not self._is_local_commit(candidate):
                unmet.append("candidate_sha_not_local_commit")
            elif not self._has_candidate_binding(
                release_id, str(evidence["Task-Branch"]), str(evidence["Base-SHA"]), candidate
            ):
                unmet.append("candidate_not_bound_to_current_branch_base")

        state = None
        store = LegacyLifecycleStore(self.repo_root)
        if store.exists(release_id):
            try:
                state = store.load(release_id)
            except LifecycleError as exc:
                # Preserve the typed fail-closed reason so callers can distinguish
                # malformed JSON/schema from an invalid autonomous activation.
                unmet.append(exc.code)
            else:
                unmet.extend(self._validate_lifecycle_state_for_audit(state, evidence, require_terminal_state))
                if evidence_version == 2 and evidence is not None:
                    unmet.extend(self._validate_v2_package_evidence(
                        release_id, release_path, state, evidence, require_terminal_state
                    ))

        test_result = None
        if strict:
            test_result = RuntimeTestRunner.run_tests(self.repo_root, explicit_python)
            if (not test_result.get("executed") or not test_result.get("passed")
                    or re.search(r"Ran\s+0\s+tests", str(test_result.get("output", "")))):
                unmet.append("strict_regression_failed")
        else:
            unmet.append("strict_audit_not_run")
        return self._lifecycle_result(release_id, unmet, test_result)

    def lifecycle_store(self) -> LegacyLifecycleStore:
        return LegacyLifecycleStore(self.repo_root)

    def _core_controller(self, release_id: str) -> CoreLifecycleController:
        if CoreLifecycleStore is None:
            raise LifecycleError("lifecycle_core_unavailable", "v0.5 lifecycle core is unavailable")
        LegacyLifecycleStore.validate_release_id(release_id)
        try:
            return CoreLifecycleController(CoreLifecycleStore(self.repo_root, release_id))
        except Exception as exc:
            raise LifecycleError("lifecycle_state_malformed", "core lifecycle state is unavailable") from exc

    @staticmethod
    def _core_status_payload(state: Dict[str, object], unmet: Optional[List[str]] = None) -> Dict[str, object]:
        identity = state.get("identity", {})
        progress = state.get("progress", {})
        control = state.get("control", {})
        no_progress = control.get("no_progress", {})
        unique = list(dict.fromkeys(unmet or []))
        return {
            "ok": not bool(unique),
            "schema_version": state.get("schema_version", 1),
            "release_id": identity.get("release_id"),
            "tier": identity.get("tier"),
            "stage": progress.get("stage"),
            "status": progress.get("status"),
            "continuation_policy": progress.get("continuation_policy"),
            "target": progress.get("target_checkpoint"),
            "current_action": progress.get("current_action"),
            "current_worker": (control.get("in_flight") or {}).get("worker_id") if isinstance(control.get("in_flight"), dict) else None,
            "no_progress": {
                "count": no_progress.get("count", 0),
                "max": no_progress.get("max", 5),
                "fingerprint": no_progress.get("stage_loop_fingerprint") or "stage-1:plan",
            },
            "budget": control.get("budget", {}),
            "last_checkpoint": progress.get("last_checkpoint"),
            "loop_record": control.get("loop_record") if isinstance(control, dict) else None,
            "unmet_conditions": unique,
            "next_action": unique[0] if unique else progress.get("next_action"),
        }

    def lifecycle_status(self, release_id: str) -> Dict[str, object]:
        return self._core_status_payload(self._core_controller(release_id).state)

    def lifecycle_start(
        self,
        release_id: str,
        policy: str = "interactive",
        target: str = "full",
        attestation: object = None,
    ) -> Dict[str, object]:
        release_path = self._release_dir(release_id)
        if not self._safe_release_directory(release_path):
            raise LifecycleError("release_artifacts_missing", "release directory does not exist or is unsafe")
        result = self.check_release(release_path, strict=False)
        if policy not in {"interactive", "autonomous"}:
            raise LifecycleError("invalid_lifecycle_policy", "policy is invalid")
        if policy == "interactive" and attestation is not None:
            raise LifecycleError("unexpected_attestation", "interactive lifecycle cannot carry autonomous attestation")
        branch = self._git_branch(self.repo_root)
        base = LegacyLifecycleStore._git_sha(self.repo_root) or ""
        controller = CoreLifecycleController.start(
            self.repo_root, release_id, tier=f"Tier {result.tier or 2}", branch=branch,
            base_sha=base, target_checkpoint=target,
        )
        if policy == "autonomous":
            if attestation is not None:
                activation = LegacyLifecycleStore.validate_attestation(attestation, release_id, policy, target)
                parsed = ActivationAttestation.from_mapping(activation)
                key = os.environ.get("FORGEFLOW_ATTESTATION_KEY", "")
                trust_anchor_id = os.environ.get("FORGEFLOW_TRUST_ANCHOR_ID")
                if not trust_anchor_id or parsed.trust_anchor_id != trust_anchor_id:
                    raise LifecycleError("autonomous_attestation_unverified", "trust anchor is not pinned")
                verifier = HMACAttestationVerifier({parsed.key_id: key}, trust_anchor_id=trust_anchor_id)
                controller.activate(AutonomousPolicy.autonomous(target), parsed, verifier)
            elif os.environ.get("FORGEFLOW_REQUIRE_HIGH_ASSURANCE") == "true":
                raise LifecycleError("autonomous_activation_unverified", "autonomous lifecycle requires verified activation attestation in high-assurance mode")
            else:
                controller.activate(AutonomousPolicy.autonomous(target))
        return self._core_status_payload(controller.state)

    def lifecycle_advance(
        self,
        release_id: str,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        action: Optional[str] = None,
        checkpoint: Optional[str] = None,
        worker: Optional[str] = None,
        invocation_id: Optional[str] = None,
        attempt_id: Optional[str] = None,
        candidate_sha: Optional[str] = None,
    ) -> Dict[str, object]:
        controller = self._core_controller(release_id)
        state = controller.state
        progress = state["progress"]
        if progress["status"] in {"PAUSED", "SUSPENDED", "BLOCKED", "TARGET_REACHED", "COMPLETE"}:
            raise LifecycleError("lifecycle_not_active", "paused, suspended, blocked, or terminal state requires resume or completion command")
        normalized_stage = stage or str(progress["stage"])
        if status is not None and status not in {"ACTIVE", "WAITING_INTERNAL"}:
            raise LifecycleError("invalid_status_transition", "advance may only select ACTIVE or WAITING_INTERNAL")
        if checkpoint is not None and checkpoint not in {"C0", "D1", "C1", "C2", "C3", "C4"}:
            raise LifecycleError("invalid_checkpoint", "checkpoint is invalid")
        if action is not None and (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", action)):
            raise LifecycleError("invalid_action", "action must be a safe code")
        if worker is not None and not LegacyLifecycleStore._SAFE_CODE.fullmatch(worker):
            raise LifecycleError("invalid_worker", "worker must be a safe code")
        if worker is not None and (not invocation_id or not attempt_id):
            raise LifecycleError(
                "worker_dispatch_identity_incomplete",
                "worker dispatch requires invocation and attempt identity",
            )
        if candidate_sha is not None and not LegacyLifecycleStore._SHA.fullmatch(candidate_sha):
            raise LifecycleError("invalid_candidate_sha", "candidate SHA must be a 40-character lowercase hex SHA")
        if action is None and normalized_stage != str(progress["stage"]):
            action = self._next_action_for(normalized_stage, checkpoint)
        return self._core_status_payload(controller.advance(
            stage=normalized_stage,
            status=status,
            action=action,
            checkpoint=checkpoint,
            worker_id=worker,
            invocation_id=invocation_id,
            attempt_id=attempt_id,
            candidate_sha=candidate_sha,
        ))

    def lifecycle_package_review(self, release_id: str, qa_sha: str) -> Dict[str, object]:
        controller = self._core_controller(release_id)
        if (controller.status == CoreStatus.PACKAGE_REVIEW_PENDING
                and controller.state["identity"].get("qa_sha") == qa_sha):
            return self._core_status_payload(controller.state)
        release_path = self._release_dir(release_id)
        qa_text = self._read_regular_text(release_path / "QA_SIGNOFF.md")
        if qa_text is None:
            raise LifecycleError("qa_signoff_unreadable", "QA Sign-off is unreadable")
        try:
            evidence = self._parse_evidence_v2(qa_text)
            self._validate_evidence_v2(release_id, qa_text, evidence)
        except ValueError as exc:
            raise LifecycleError("qa_evidence_malformed", str(exc)) from exc
        if evidence["QA-SHA"] != qa_sha or not self._is_local_commit(qa_sha):
            raise LifecycleError("qa_sha_invalid", "QA SHA does not identify the approved local snapshot")
        expected_branch = controller.state["identity"].get("branch")
        evidence_branch = str(evidence.get("Task-Branch", ""))
        if expected_branch and evidence_branch != expected_branch:
            raise LifecycleError("evidence_branch_mismatch", f"evidence Task-Branch '{evidence_branch}' does not match lifecycle state branch '{expected_branch}'")
        reviewer_dict = {"security": "APPROVED", "reliability": "APPROVED", "maintainability": "APPROVED"}
        for r_val in evidence.get("Reviewer", []):
            try:
                r_item = self._pairs(str(r_val), {"id", "perspective", "verdict", "qa-sha"})
                reviewer_dict[r_item["id"]] = r_item["verdict"]
            except Exception:
                pass
        self._check_package_artifacts_integrity(release_id, release_path, require_completion_report=False)
        controller.update_evidence(
            gate1="APPROVED", gate2="APPROVED",
            reviewers=reviewer_dict,
            verification={"passed": True},
        )
        return self._core_status_payload(controller.mark_package_review_pending(qa_sha=qa_sha))

    def lifecycle_seal(self, release_id: str, release_candidate_sha: str) -> Dict[str, object]:
        controller = self._core_controller(release_id)
        release_path = self._release_dir(release_id)
        qa_text = self._read_regular_text(release_path / "QA_SIGNOFF.md")
        if qa_text is None:
            raise LifecycleError("qa_signoff_unreadable", "QA Sign-off is unreadable")
        try:
            evidence = self._parse_evidence_v2(qa_text)
            self._validate_evidence_v2(release_id, qa_text, evidence)
            manifest, _ = self._package_manifest(release_id, release_path)
        except ValueError as exc:
            raise LifecycleError("package_evidence_malformed", str(exc)) from exc

        self._check_package_artifacts_integrity(release_id, release_path, require_completion_report=True)

        signoff = self._read_regular_text(release_path / "RELEASE_SIGNOFF.md")
        if signoff is None:
            raise LifecycleError("release_signoff_unreadable", "RELEASE_SIGNOFF.md is unreadable or missing")
        match = re.search(r"(?ms)^## ForgeFlow Release Sign-off v1\n(?:\n)?```text\n(.*?)^```\s*$", signoff)
        if not match:
            raise LifecycleError("release_signoff_malformed", "RELEASE_SIGNOFF.md block is malformed")
        values = {}
        for line in match.group(1).splitlines():
            if ": " not in line:
                raise LifecycleError("release_signoff_malformed", "RELEASE_SIGNOFF.md line format invalid")
            key, value = line.split(": ", 1)
            if key in values:
                raise LifecycleError("release_signoff_malformed", f"duplicate key {key} in RELEASE_SIGNOFF.md")
            values[key] = value

        if (values.get("Release-ID") != release_id
                or values.get("Gate-3") != "APPROVED"
                or values.get("User-Verdict") != "GO"):
            raise LifecycleError("release_signoff_not_approved", "RELEASE_SIGNOFF.md requires Gate-3: APPROVED and User-Verdict: GO")
        if values.get("Package-Manifest-SHA256") != manifest:
            raise LifecycleError("package_manifest_mismatch", f"Package-Manifest-SHA256 in RELEASE_SIGNOFF.md ({values.get('Package-Manifest-SHA256')}) does not match current manifest ({manifest})")

        if (controller.state["identity"].get("candidate_sha") == release_candidate_sha
                and controller.state["evidence"].get("package_manifest_sha256") == manifest
                and controller.state["evidence"].get("package_seal") == "SEALED"
                and controller.status == CoreStatus.PACKAGE_SEALED):
            return self._core_status_payload(controller.state)

        if controller.status not in {CoreStatus.PACKAGE_REVIEW_PENDING, CoreStatus.PACKAGE_SEALED}:
            raise LifecycleError("package_review_not_pending", "Release candidate may be sealed only after QA Sign-off package review state")
        if not self._has_v2_candidate_binding(release_id, str(evidence["QA-SHA"]), release_candidate_sha):
            raise LifecycleError("release_candidate_not_local_commit", "release candidate is not a valid local commit")
        controller.update_evidence(gate3="APPROVED")
        return self._core_status_payload(controller.seal_package(
            release_candidate_sha=release_candidate_sha, package_manifest_sha256=manifest
        ))

    def lifecycle_record_attempt(
        self,
        release_id: str,
        result: str,
        attempt_id: str,
        stage_loop_fingerprint: Optional[str] = None,
        worker: Optional[str] = None,
    ) -> Dict[str, object]:
        controller = self._core_controller(release_id)
        state = controller.state
        if state["progress"]["status"] in {"PAUSED", "SUSPENDED", "BLOCKED", "TARGET_REACHED", "COMPLETE"}:
            raise LifecycleError("lifecycle_terminal", "terminal lifecycle cannot record an attempt")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", attempt_id):
            raise LifecycleError("invalid_attempt_id", "attempt ID must be a safe code")
        aliases = {"passed": "progress", "success": "progress", "pass": "progress", "failed": "no-progress", "failure": "no-progress", "fail": "no-progress"}
        result = aliases.get(result, result)
        if result not in {"progress", "no-progress", "duplicate", "timeout"}:
            raise LifecycleError("invalid_attempt_result", "attempt result is invalid")
        fingerprint = stage_loop_fingerprint or str(state["control"]["no_progress"].get("stage_loop_fingerprint") or "stage-1:plan")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", fingerprint):
            raise LifecycleError("invalid_stage_loop_fingerprint", "stage loop fingerprint is invalid")
        if worker is not None and not LegacyLifecycleStore._SAFE_CODE.fullmatch(worker):
            raise LifecycleError("invalid_worker", "worker must be a safe code")
        updated = controller.record_attempt(
            stage_loop_fingerprint=fingerprint,
            attempt_class=attempt_id if worker is None else f"{attempt_id}:{worker}",
            progress=result == "progress",
            remediation=result == "no-progress",
            duplicate=result in {"duplicate", "timeout"},
            failure=result,
            next_action="remediate_no_progress" if result == "no-progress" else "reconcile_worker_attempt",
        )
        return self._core_status_payload(updated)

    def lifecycle_resume(self, release_id: str, policy: str, target: Optional[str] = None, attestation: object = None) -> Dict[str, object]:
        controller = self._core_controller(release_id)
        state = controller.state
        if state["progress"]["status"] not in {"PAUSED", "SUSPENDED", "BLOCKED"}:
            raise LifecycleError("lifecycle_not_resumable", "only paused, suspended, or blocked lifecycle can resume")
        if policy not in {"interactive", "autonomous"}:
            raise LifecycleError("invalid_lifecycle_policy", "resume requires an explicit policy")
        selected_target = target or str(state["progress"]["target_checkpoint"])
        if selected_target not in {"design-only", "full", "current-stage"}:
            raise LifecycleError("invalid_lifecycle_target", "target is invalid")
        if policy == "autonomous":
            activation = LegacyLifecycleStore.validate_attestation(attestation, release_id, policy, selected_target)
            parsed = ActivationAttestation.from_mapping(activation)
            trust_anchor_id = os.environ.get("FORGEFLOW_TRUST_ANCHOR_ID")
            if not trust_anchor_id or parsed.trust_anchor_id != trust_anchor_id:
                raise LifecycleError("autonomous_attestation_unverified", "trust anchor is not pinned")
            verifier = HMACAttestationVerifier(
                {parsed.key_id: os.environ["FORGEFLOW_ATTESTATION_KEY"]},
                trust_anchor_id=trust_anchor_id,
            )
            updated = controller.resume(AutonomousPolicy.autonomous(selected_target), parsed, verifier)
        else:
            updated = controller._update(lambda current: current["progress"].update(
                continuation_policy="interactive", target_checkpoint=selected_target,
                next_action="resume_current_stage"))
            updated = controller.transition(CoreStatus.ACTIVE, reason="explicit interactive resume", resume=True)
        return self._core_status_payload(updated)

    def lifecycle_complete(self, release_id: str, explicit_python: Optional[str] = None) -> Dict[str, object]:
        controller = self._core_controller(release_id)
        state = controller.state
        if state["progress"]["status"] == "COMPLETE":
            return self._core_status_payload(state)
        if state["progress"]["status"] in {"TARGET_REACHED"}:
            raise LifecycleError("lifecycle_terminal", "lifecycle is already terminal")
        unmet: List[str] = []
        if state["progress"].get("last_checkpoint") != "C4":
            unmet.append("completion_checkpoint_missing:C4")

        can_reuse_strict_audit = False
        candidate = state["identity"].get("candidate_sha")
        strict_audit_ev = state["evidence"].get("strict_audit")
        if (isinstance(strict_audit_ev, dict)
                and strict_audit_ev.get("passed") is True
                and candidate is not None
                and self._is_local_commit(candidate)):
            try:
                head = subprocess.run(["git", "-C", str(self.repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
                status = subprocess.run(["git", "-C", str(self.repo_root), "status", "--porcelain"], capture_output=True, text=True, check=False)
                if head.returncode == 0 and head.stdout.strip() == candidate and status.returncode == 0 and not status.stdout.strip():
                    release_path = self._release_dir(release_id)
                    manifest, _ = self._package_manifest(release_id, release_path)
                    if state["evidence"].get("package_manifest_sha256") == manifest:
                        can_reuse_strict_audit = True
            except Exception:
                pass

        # Atomic transition from in-progress to completed if layout is tasks or ff-tasks
        rel_dir = self._release_dir(release_id)
        try:
            rel = rel_dir.relative_to(self.repo_root)
            parts = rel.parts
            valid_tasks_roots = {"tasks", "ff-tasks"}
            configured = ReleaseScanner._read_configured_tasks_dir(self.repo_root)
            if configured:
                valid_tasks_roots.add(configured)
            if len(parts) >= 3 and parts[0] in valid_tasks_roots and parts[1] == "in-progress":
                completed_dest = self.repo_root / parts[0] / "completed" / release_id
                completed_dest.parent.mkdir(parents=True, exist_ok=True)
                if not completed_dest.exists():
                    import shutil
                    shutil.move(str(rel_dir), str(completed_dest))
        except Exception:
            pass

        strict_flag = not can_reuse_strict_audit
        audit = self.check_lifecycle_evidence(release_id, strict=strict_flag, explicit_python=explicit_python, require_terminal_state=False)
        unmet.extend(audit["unmet_conditions"])
        if candidate is not None:
            qa = self._read_regular_text(self._release_dir(release_id) / "QA_SIGNOFF.md") or ""
            if "## ForgeFlow Evidence v2" not in qa:
                try:
                    evidence = self._parse_evidence_block(qa)
                    if evidence.get("Candidate-SHA") != candidate:
                        unmet.append("lifecycle_candidate_mismatch")
                except ValueError:
                    pass
        loop_record = state.get("control", {}).get("loop_record")
        if loop_record and isinstance(loop_record, dict):
            open_remediations = [r for r in loop_record.get("remediations", []) if r.get("status") == "OPEN"]
            if open_remediations or loop_record.get("latest_verdict") in {"REJECT", "FAIL"}:
                unmet.append("unresolved_remediation_active")
            if loop_record.get("terminal_reason") == "circuit-breaker":
                unmet.append("circuit_breaker_tripped")
        if unmet:
            return self._core_status_payload(state, list(dict.fromkeys(unmet)))
        updated = controller._update(lambda current: current["progress"].update(
            last_checkpoint="C4", next_action="terminal"))
        updated = controller.update_evidence(strict_audit={"passed": True, "reused": can_reuse_strict_audit}, gate2="APPROVED")
        updated = controller.transition(CoreStatus.COMPLETE, reason="all completion guards satisfied")
        return self._core_status_payload(updated)

    def lifecycle_close(self, release_id: str) -> Dict[str, object]:
        controller = self._core_controller(release_id)
        state = controller.state
        if state["progress"]["status"] != "COMPLETE":
            raise LifecycleError("lifecycle_not_complete", f"release '{release_id}' is not in COMPLETE state")

        if self._is_git_detached(self.repo_root):
            raise LifecycleError("worktree_detached_head", "current worktree is in detached HEAD state; lifecycle close requires 'main' branch")

        branch = self._git_branch(self.repo_root)
        if branch != "main":
            raise LifecycleError("not_on_main_branch", f"current branch is '{branch}', but lifecycle close requires 'main'")

        try:
            status = subprocess.run(
                ["git", "-C", str(self.repo_root), "status", "--porcelain"],
                capture_output=True, text=True, check=False,
            )
            if status.returncode != 0:
                raise LifecycleError("git_command_failed", "failed to check git status")
            dirty = [
                line[3:].strip() for line in status.stdout.splitlines()
                if line.strip() and not line[3:].strip().endswith(".lock")
            ]
            if dirty:
                raise LifecycleError("worktree_not_clean", "working tree must be clean to close release")
        except OSError as exc:
            raise LifecycleError("git_command_failed", f"failed to check git status: {exc}") from exc

        task_branch = state.get("identity", {}).get("branch")
        if not task_branch or task_branch in {"main", "master"}:
            task_branch = f"feat/{release_id}"

        worktrees = self._get_worktrees(self.repo_root)
        for wt in worktrees:
            wt_path_str = wt.get("worktree")
            if not wt_path_str:
                continue
            if wt.get("branch") == task_branch:
                raise LifecycleError(
                    "task_branch_checked_out_in_worktree",
                    f"task branch '{task_branch}' is currently checked out at worktree '{wt_path_str}'. "
                    f"Please switch or remove that worktree before closing release '{release_id}'."
                )

        branch_cleaned = False
        deleted_branch = None
        if task_branch not in {"main", "master"}:
            try:
                check_ref = subprocess.run(
                    ["git", "-C", str(self.repo_root), "rev-parse", "--verify", f"refs/heads/{task_branch}"],
                    capture_output=True, text=True, check=False,
                )
                if check_ref.returncode == 0:
                    del_res = subprocess.run(
                        ["git", "-C", str(self.repo_root), "branch", "-d", task_branch],
                        capture_output=True, text=True, check=False,
                    )
                    if del_res.returncode != 0:
                        raise LifecycleError("branch_delete_failed", f"failed to safely delete branch '{task_branch}': {del_res.stderr.strip()}")
                    branch_cleaned = True
                    deleted_branch = task_branch
            except OSError as exc:
                raise LifecycleError("git_command_failed", f"failed to run git branch: {exc}") from exc

        if self._is_git_detached(self.repo_root):
            raise LifecycleError("worktree_detached_head", "worktree left in detached HEAD state after closing release")
        post_branch = self._git_branch(self.repo_root)
        if post_branch != "main":
            raise LifecycleError("not_on_main_branch", f"worktree branch is '{post_branch}', expected 'main' after close")

        try:
            status_post = subprocess.run(
                ["git", "-C", str(self.repo_root), "status", "--porcelain"],
                capture_output=True, text=True, check=False,
            )
            if status_post.returncode == 0:
                dirty_post = [
                    line[3:].strip() for line in status_post.stdout.splitlines()
                    if line.strip() and not line[3:].strip().endswith(".lock")
                ]
                if dirty_post:
                    raise LifecycleError("worktree_not_clean", "working tree must remain clean after closing release")
        except OSError as exc:
            raise LifecycleError("git_command_failed", f"failed to verify git status: {exc}") from exc

        msg = "branch cleaned up, working tree clean." if branch_cleaned else "branch already cleaned up, working tree clean."
        return {
            "schema_version": 1,
            "release_id": release_id,
            "ok": True,
            "status": "CLOSED",
            "branch_cleaned": branch_cleaned,
            "deleted_branch": deleted_branch,
            "message": msg,
        }

    @staticmethod
    def _is_git_detached(repo_root: Path) -> bool:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), "symbolic-ref", "-q", "HEAD"],
                capture_output=True, text=True, check=False,
            )
            return result.returncode != 0
        except OSError:
            return False

    @classmethod
    def _get_worktrees(cls, repo_root: Path) -> List[Dict[str, object]]:
        try:
            res = subprocess.run(
                ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"],
                capture_output=True, text=True, check=False,
            )
            if res.returncode != 0:
                return []
            worktrees: List[Dict[str, object]] = []
            current: Dict[str, object] = {}
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line:
                    if current:
                        worktrees.append(current)
                        current = {}
                    continue
                if line.startswith("worktree "):
                    if current:
                        worktrees.append(current)
                        current = {}
                    current["worktree"] = line[len("worktree "):].strip()
                    current["detached"] = False
                    current["bare"] = False
                    current["branch"] = None
                elif line.startswith("HEAD "):
                    current["HEAD"] = line[len("HEAD "):].strip()
                elif line.startswith("branch "):
                    ref = line[len("branch "):].strip()
                    if ref.startswith("refs/heads/"):
                        ref = ref[len("refs/heads/"):]
                    current["branch"] = ref
                elif line == "detached":
                    current["detached"] = True
                elif line == "bare":
                    current["bare"] = True
            if current:
                worktrees.append(current)
            return worktrees
        except OSError:
            return []

    @staticmethod
    def _git_branch(repo_root: Path) -> str:
        try:
            result = subprocess.run(["git", "-C", str(repo_root), "branch", "--show-current"], capture_output=True, text=True, check=False)
        except OSError:
            return ""
        return result.stdout.strip() if result.returncode == 0 else ""

    @staticmethod
    def _next_action_for(stage: str, checkpoint: Optional[str]) -> str:
        if checkpoint == "C4" or stage == "GATE_2":
            return "run Gate 2 and complete"
        if checkpoint == "D1":
            return "implement reviewed scope"
        if checkpoint == "C0":
            return "verify reviewed digest and create D1"
        return {"STAGE_1": "complete Gate 1 and create C0", "GATE_1": "create clean worktree and C0", "STAGE_3": "verify reviewed digest and create D1", "STAGE_4": "run implementation verification"}.get(stage, "resume_current_stage")

    @staticmethod
    def compute_failure_fingerprint(context: str, details: Any = None) -> str:
        raw_text = str(context)
        if details is not None:
            if isinstance(details, (list, tuple)):
                raw_text += "::" + "::".join(str(item) for item in details)
            elif isinstance(details, dict):
                raw_text += "::" + json.dumps(details, sort_keys=True, ensure_ascii=False)
            else:
                raw_text += f"::{details}"
        normalized = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", raw_text)
        normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", "<TIMESTAMP>", normalized)
        normalized = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "<UUID>", normalized)
        normalized = re.sub(r"(?:/tmp|/var/folders/[^/]+/[^/]+/T)/[a-zA-Z0-9_\-]+", "<TMP_PATH>", normalized)
        return hashlib.sha256(normalized.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_lifecycle_state_for_audit(state: Dict[str, object], evidence: Optional[Dict[str, object]], require_terminal_state: bool) -> List[str]:
        unmet: List[str] = []
        core_state = "progress" in state
        progress = state["progress"] if core_state else state
        identity = state["identity"] if core_state else state
        control = state.get("control", {}) if core_state else state
        if progress["continuation_policy"] == "autonomous":
            loop_record = control.get("loop_record") if isinstance(control, dict) else None
            is_lightweight = isinstance(loop_record, dict) and os.environ.get("FORGEFLOW_REQUIRE_HIGH_ASSURANCE") != "true"
            raw = state["host"].get("attestation") if core_state else state.get("activation_attestation")
            if not is_lightweight or raw is not None:
                try:
                    LegacyLifecycleStore.validate_attestation(raw, str(identity["release_id"]), "autonomous", str(progress["target_checkpoint"]))
                except LifecycleError as exc:
                    unmet.append(exc.code)
        loop_record = control.get("loop_record") if isinstance(control, dict) else None
        if loop_record and isinstance(loop_record, dict):
            open_remediations = [r for r in loop_record.get("remediations", []) if r.get("status") == "OPEN"]
            if open_remediations or loop_record.get("latest_verdict") in {"REJECT", "FAIL"}:
                if require_terminal_state or progress.get("status") == "COMPLETE":
                    unmet.append("unresolved_remediation_active")
            if loop_record.get("terminal_reason") == "circuit-breaker":
                unmet.append("circuit_breaker_tripped")
        if evidence is not None:
            if "QA-SHA" in evidence:
                if identity.get("qa_sha") != evidence.get("QA-SHA"):
                    unmet.append("lifecycle_qa_sha_mismatch")
            elif identity.get("candidate_sha") != evidence.get("Candidate-SHA"):
                unmet.append("lifecycle_candidate_mismatch")
        status = progress["status"]
        last_checkpoint = progress.get("last_checkpoint")
        next_action = progress.get("next_action")
        if require_terminal_state and status != "COMPLETE":
            unmet.append("lifecycle_not_complete")
        if status == "COMPLETE" and (last_checkpoint != "C4" or next_action not in {None, "terminal"}):
            unmet.append("lifecycle_completion_guard_unmet")
        return unmet

    @staticmethod
    def _read_regular_text(path: Path) -> Optional[str]:
        try:
            if path.is_symlink() or not path.is_file():
                return None
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return None

    def _safe_release_directory(self, release_path: Path) -> bool:
        """Accept only a repository-contained directory tree without symlinks."""
        try:
            release_path.relative_to(self.repo_root)
            relative = release_path.relative_to(self.repo_root)
            current = self.repo_root
            for component in relative.parts:
                current = current / component
                if current.is_symlink() or not current.is_dir():
                    return False
            return True
        except (OSError, ValueError):
            return False

    _EVIDENCE_HEADING = "## ForgeFlow Evidence v1"
    _CORE_ARTIFACTS = ("PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md")
    _SHA = re.compile(r"[0-9a-f]{40}")
    _DIGEST = re.compile(r"[0-9a-f]{64}")
    _ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
    _BRANCH = re.compile(r"^(?!.*(?:\.\.|//))[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")

    @classmethod
    def _parse_evidence_v2(cls, text: str) -> Dict[str, object]:
        heading = "## ForgeFlow Evidence v2"
        pattern = re.compile(rf"(?ms)^{re.escape(heading)}\n(?:\n)?```text\n(.*?)^```\s*$")
        matches = list(pattern.finditer(text))
        if len(matches) != 1 or text.count(heading) != 1:
            raise ValueError("evidence_v2_block_count: QA_SIGNOFF.md requires exactly one '## ForgeFlow Evidence v2' section with a text code block")
        fields: Dict[str, object] = {"Reviewer": [], "Verification": []}
        singleton = {"Schema-Version", "Release-ID", "Tier", "Task-Branch", "Base-SHA", "QA-SHA", "Stage", "Gate-1", "Gate-2", "Next-Action"}
        for raw in matches[0].group(1).splitlines():
            if not raw or raw != raw.strip() or ":" not in raw:
                raise ValueError("evidence_v2_line_shape: lines in Evidence v2 must match 'Key: Value'")
            key, value = raw.split(":", 1)
            if key not in singleton | {"Reviewer", "Verification"} or not value.startswith(" ") or not value[1:]:
                raise ValueError(f"evidence_v2_field_shape: malformed field '{key}'")
            if key in singleton:
                if key in fields:
                    raise ValueError(f"evidence_v2_duplicate: duplicate field '{key}'")
                fields[key] = value[1:]
            else:
                fields[key].append(value[1:])  # type: ignore[index]
        missing = singleton - set(fields)
        if missing:
            raise ValueError("evidence_v2_missing_" + sorted(missing)[0].lower())
        return fields

    @classmethod
    def _validate_evidence_v2(cls, release_id: str, qa_text: str, evidence: Dict[str, object]) -> None:
        if (evidence.get("Schema-Version") != "2" or evidence.get("Release-ID") != release_id
                or evidence.get("Tier") not in {"2", "3"} or evidence.get("Stage") != "PACKAGE_REVIEW_PENDING"
                or evidence.get("Gate-1") != "APPROVED" or evidence.get("Gate-2") != "APPROVED"
                or evidence.get("Next-Action") not in {"RELEASE_SIGNOFF", "PACKAGE_REVIEW"}):
            raise ValueError("evidence_v2_binding")
        qa_sha = str(evidence.get("QA-SHA", ""))
        if not cls._SHA.fullmatch(qa_sha) or not cls._SHA.fullmatch(str(evidence.get("Base-SHA", ""))) or not cls._BRANCH.fullmatch(str(evidence.get("Task-Branch", ""))):
            raise ValueError("evidence_v2_sha_shape")
        tier = str(evidence.get("Tier", "3"))
        reviewers = evidence.get("Reviewer")
        min_reviewers = 3 if tier == "3" else 1
        if not isinstance(reviewers, list) or len(reviewers) < min_reviewers:
            raise ValueError("evidence_v2_reviewer_count")
        identities, perspectives = set(), set()
        for value in reviewers:
            item = cls._pairs(str(value), {"id", "perspective", "verdict", "qa-sha"})
            if not cls._ID.fullmatch(item["id"]) or item["verdict"] != "APPROVED" or item["qa-sha"] != qa_sha:
                raise ValueError("evidence_v2_reviewer_shape")
            if item["id"] in identities:
                raise ValueError("evidence_v2_reviewer_duplicate")
            identities.add(item["id"])
            perspectives.add(item["perspective"])
        if tier == "3" and not {"Security", "Reliability", "Maintainability"}.issubset(perspectives):
            raise ValueError("evidence_v2_reviewer_identity")
        verifications = evidence.get("Verification")
        if not isinstance(verifications, list) or not verifications:
            raise ValueError("evidence_v2_verification_missing")
        for value in verifications:
            item = cls._pairs(str(value), {"id", "command", "result", "exit-code", "qa-sha"}, optional={"output-digest", "digest"})
            if (not cls._ID.fullmatch(item["id"]) or not item["command"].strip()
                    or item["result"] != "PASS" or item["exit-code"] != "0" or item["qa-sha"] != qa_sha):
                raise ValueError("evidence_v2_verification_shape")
            if "output-digest" in item and not (cls._DIGEST.fullmatch(item["output-digest"]) or cls._SHA.fullmatch(item["output-digest"])):
                raise ValueError("evidence_v2_verification_digest_shape")
            if "digest" in item and not (cls._DIGEST.fullmatch(item["digest"]) or cls._SHA.fullmatch(item["digest"])):
                raise ValueError("evidence_v2_verification_digest_shape")

    def _check_package_artifacts_integrity(self, release_id: str, release_path: Path, *, require_completion_report: bool = False) -> None:
        names = ["PRD.md", "DESIGN.md", "QA_SIGNOFF.md"]
        if require_completion_report:
            names.append("COMPLETION_REPORT.md")
        for name in names:
            content = self._read_regular_text(release_path / name)
            if content is None:
                raise LifecycleError("package_artifact_missing", f"required package artifact '{name}' is missing or unreadable")
            if self._contains_placeholder(content):
                raise LifecycleError("package_artifact_incomplete", f"package artifact '{name}' contains unresolved placeholder content")

        design_content = self._read_regular_text(release_path / "DESIGN.md") or ""
        design_lower = design_content.lower()
        if not ("rtm" in design_lower or "requirements traceability matrix" in design_lower or "요구사항 추적" in design_lower):
            raise LifecycleError("design_incomplete", "DESIGN.md is missing Requirements Traceability Matrix (RTM)")
        if not ("gate 1" in design_lower):
            raise LifecycleError("design_incomplete", "DESIGN.md is missing Gate 1 Review / Verdict")

        if require_completion_report:
            comp_content = self._read_regular_text(release_path / "COMPLETION_REPORT.md") or ""
            if len(comp_content.strip().splitlines()) < 5:
                raise LifecycleError("completion_report_incomplete", "COMPLETION_REPORT.md is incomplete or too short")

    def _package_manifest(self, release_id: str, release_path: Path) -> tuple[str, set[str]]:
        names = ["PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md"]
        notes = release_path / "RELEASE_NOTES.md"
        if notes.exists():
            names.append("RELEASE_NOTES.md")
        rows = []
        for name in names:
            content = self._read_regular_text(release_path / name)
            if content is None or self._contains_placeholder(content):
                raise ValueError("package_manifest_artifact_invalid")
            rows.append(f"{name}:{hashlib.sha256(content.encode('utf-8')).hexdigest()}")
        return hashlib.sha256(("\n".join(rows) + "\n").encode("utf-8")).hexdigest(), set(names)

    def _validate_v2_package_evidence(self, release_id: str, release_path: Path, state: Dict[str, object], evidence: Dict[str, object], require_terminal_state: bool) -> List[str]:
        unmet: List[str] = []
        identity = state.get("identity", {}) if isinstance(state.get("identity"), dict) else {}
        progress = state.get("progress", {}) if isinstance(state.get("progress"), dict) else {}
        details = state.get("evidence", {}) if isinstance(state.get("evidence"), dict) else {}
        if identity.get("qa_sha") != evidence.get("QA-SHA"):
            unmet.append("qa_sha_mismatch")
        signoff = self._read_regular_text(release_path / "RELEASE_SIGNOFF.md")
        if signoff is None:
            return unmet + ["release_signoff_unreadable"]
        match = re.search(r"(?ms)^## ForgeFlow Release Sign-off v1\n(?:\n)?```text\n(.*?)^```\s*$", signoff)
        if not match:
            return unmet + ["release_signoff_malformed"]
        values = {}
        for line in match.group(1).splitlines():
            if ": " not in line:
                return unmet + ["release_signoff_malformed"]
            key, value = line.split(": ", 1)
            if key in values:
                return unmet + ["release_signoff_malformed"]
            values[key] = value
        try:
            manifest, _ = self._package_manifest(release_id, release_path)
        except ValueError as exc:
            return unmet + [str(exc)]
        if values.get("Release-ID") != release_id or values.get("Gate-3") != "APPROVED" or values.get("User-Verdict") != "GO":
            unmet.append("release_signoff_not_approved")
        if values.get("Package-Manifest-SHA256") != manifest:
            unmet.append("package_manifest_mismatch")
        if details.get("package_seal") == "SEALED" and details.get("package_manifest_sha256") != manifest:
            try:
                controller = self._core_controller(release_id)
                controller.unseal_package(reason="package manifest mismatch: artifacts mutated after seal")
            except Exception:
                pass
            unmet.append("package_manifest_mismatch")
            unmet.append("package_seal_mismatch")
        if require_terminal_state:
            candidate = identity.get("candidate_sha")
            if not isinstance(candidate, str) or not self._SHA.fullmatch(candidate):
                unmet.append("release_candidate_missing")
            elif not self._has_v2_candidate_binding(release_id, str(evidence["QA-SHA"]), candidate):
                unmet.append("candidate_sha_not_local_commit")
            if details.get("package_manifest_sha256") != manifest or details.get("package_seal") != "SEALED":
                unmet.append("package_seal_mismatch")
            if progress.get("status") != "COMPLETE":
                unmet.append("lifecycle_not_complete")
        return unmet

    def _tree_files_at_commit(self, commit: str, directory_path: str) -> Dict[str, str]:
        """Deprecated per ADR 001. Maintained for interface compatibility."""
        return {}

    def _find_verified_completion_relocation_paths(self, release_id: str, candidate: str, current_head: str) -> Set[str]:
        """Deprecated per ADR 001. Maintained for interface compatibility."""
        return set()

    def _candidate_disallowed_paths(self, release_id: str, qa_sha: str, candidate: str) -> Optional[List[str]]:
        """Deprecated per ADR 001. Maintained for interface compatibility.
        
        Diff-range allowlist checks were eliminated per ADR 001 to prevent false
        positive rejections from benign commits, version bumps, or documentation.
        """
        if not self._has_v2_candidate_binding(release_id, qa_sha, candidate):
            return ["candidate_sha_not_local_commit"]
        return []

    def _has_v2_candidate_binding(self, release_id: str, qa_sha: str, candidate: str) -> bool:
        """Verify candidate is a valid SHA string and an extant local commit.
        
        Eliminates brittle commit-range diff checks per ADR 001.
        """
        if not isinstance(candidate, str) or not self._SHA.fullmatch(candidate):
            return False
        return self._is_local_commit(candidate)
    @classmethod
    def _parse_evidence_block(cls, text: str) -> Dict[str, object]:
        """Parse the one supported, deliberately small line-oriented schema.

        This parser is intentionally stricter than the normal Markdown
        validator: it accepts no inferred approvals, duplicate fields, or
        unknown fields.  The enclosing fenced block also makes the digest of
        QA_SIGNOFF well-defined (the block itself is excluded; see
        ``_artifact_digest``).
        """
        pattern = re.compile(
            rf"(?ms)^{re.escape(cls._EVIDENCE_HEADING)}\n```text\n(.*?)^```\s*$"
        )
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise ValueError("evidence_block_count")
        if text.count(cls._EVIDENCE_HEADING) != 1:
            raise ValueError("evidence_heading_duplicate")
        fields: Dict[str, object] = {"Reviewer": [], "Artifact": [], "Verification": []}
        singleton = {
            "Schema-Version", "Release-ID", "Tier", "Task-Branch", "Base-SHA",
            "Candidate-SHA", "Stage", "Gate-1", "Gate-2", "Next-Action",
        }
        allowed = singleton | {"Reviewer", "Artifact", "Verification"}
        for raw_line in matches[0].group(1).splitlines():
            if not raw_line or raw_line != raw_line.strip() or ":" not in raw_line:
                raise ValueError("evidence_line_shape")
            key, value = raw_line.split(":", 1)
            if key not in allowed or not value.startswith(" ") or not value[1:]:
                raise ValueError("evidence_field_shape")
            value = value[1:]
            if key in singleton:
                if key in fields:
                    raise ValueError(f"duplicate_{key.lower()}")
                fields[key] = value
            else:
                fields[key].append(value)  # type: ignore[index]
        missing = sorted(singleton - set(fields))
        if missing:
            raise ValueError("missing_" + missing[0].lower())
        return fields

    @classmethod
    def _pairs(cls, value: str, required: set, optional: Optional[set] = None) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for part in value.split("; "):
            if "=" not in part:
                raise ValueError("evidence_value_shape")
            key, item = part.split("=", 1)
            if not key or not item or key in pairs:
                raise ValueError("evidence_value_duplicate_or_empty")
            pairs[key] = item
        allowed = required | (optional or set())
        if not required.issubset(set(pairs)) or not set(pairs).issubset(allowed):
            raise ValueError("evidence_value_keys")
        return pairs

    @classmethod
    def _validate_evidence(
        cls, release_id: str, release_path: Path, qa_text: str, evidence: Dict[str, object]
    ) -> None:
        if evidence["Schema-Version"] != "1" or evidence["Release-ID"] != release_id:
            raise ValueError("schema_or_release_binding")
        if evidence["Tier"] != "3" or evidence["Stage"] not in {"GATE_2", "COMPLETE"}:
            raise ValueError("tier_or_stage")
        candidate = str(evidence["Candidate-SHA"])
        base = str(evidence["Base-SHA"])
        if not cls._SHA.fullmatch(candidate) or not cls._SHA.fullmatch(base) or not cls._BRANCH.fullmatch(str(evidence["Task-Branch"])):
            raise ValueError("candidate_sha_shape")
        if evidence["Gate-1"] != "APPROVED" or evidence["Gate-2"] != "APPROVED":
            raise ValueError("gate_verdict")
        if evidence["Next-Action"] != "NONE":
            raise ValueError("next_action_not_none")

        reviewers = evidence["Reviewer"]
        if not isinstance(reviewers, list) or len(reviewers) != 3:
            raise ValueError("reviewer_count")
        identities, perspectives = set(), set()
        for value in reviewers:
            item = cls._pairs(str(value), {"id", "perspective", "verdict", "candidate-sha"})
            if not cls._ID.fullmatch(item["id"]) or item["verdict"] != "APPROVED":
                raise ValueError("reviewer_shape")
            if item["candidate-sha"] != candidate:
                raise ValueError("reviewer_candidate_mismatch")
            identities.add(item["id"])
            perspectives.add(item["perspective"])
        if len(identities) != 3 or perspectives != {"Security", "Reliability", "Maintainability"}:
            raise ValueError("reviewer_identity_or_perspective")

        artifacts = evidence["Artifact"]
        if not isinstance(artifacts, list) or len(artifacts) != len(cls._CORE_ARTIFACTS):
            raise ValueError("artifact_count")
        seen_artifacts = set()
        for value in artifacts:
            item = cls._pairs(str(value), {"path", "sha256", "status"})
            path = item["path"]
            if path not in cls._CORE_ARTIFACTS or item["status"] != "COMPLETE" or not cls._DIGEST.fullmatch(item["sha256"]):
                raise ValueError("artifact_shape")
            if path in seen_artifacts:
                raise ValueError("artifact_duplicate")
            contents = cls._read_regular_text(release_path / path)
            if (contents is None or cls._contains_placeholder(contents)
                    or item["sha256"] != cls._artifact_digest(path, contents)):
                raise ValueError("artifact_unreadable_or_stale")
            seen_artifacts.add(path)
        if seen_artifacts != set(cls._CORE_ARTIFACTS):
            raise ValueError("artifact_paths")

        verifications = evidence["Verification"]
        if not isinstance(verifications, list) or not verifications:
            raise ValueError("verification_missing")
        verification_ids = set()
        for value in verifications:
            item = cls._pairs(str(value), {"id", "command", "result", "exit-code", "candidate-sha"})
            if (not cls._ID.fullmatch(item["id"]) or not item["command"].strip()
                    or item["result"] != "PASS" or item["exit-code"] != "0"
                    or item["candidate-sha"] != candidate or item["id"] in verification_ids):
                raise ValueError("verification_shape")
            verification_ids.add(item["id"])

    @classmethod
    def _artifact_digest(cls, name: str, content: str) -> str:
        # QA_SIGNOFF contains this evidence block, so hashing its literal bytes
        # would be self-referential.  Its canonical digest replaces exactly the
        # one parsed block with a fixed marker; no other content is omitted.
        if name == "QA_SIGNOFF.md":
            content, count = re.subn(
                rf"(?ms)^{re.escape(cls._EVIDENCE_HEADING)}\n```text\n.*?^```\s*$",
                cls._EVIDENCE_HEADING + "\n<evidence-omitted>\n",
                content,
            )
            if count != 1:
                raise ValueError("qa_digest_evidence_block")
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _contains_placeholder(content: str) -> bool:
        return "{{" in content or bool(re.search(
            r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?(?:status|final verdict|qa sign-off)(?:\*\*)?\s*:\s*(?:draft|pending|tbd)\b|\b(?:TODO|FIXME)\b|\bthis is a placeholder document\b",
            content,
        ))

    def _is_local_commit(self, candidate: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_root), "cat-file", "-e", f"{candidate}^{{commit}}"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return False
        return result.returncode == 0

    def _has_candidate_binding(self, release_id: str, branch: str, base: str, candidate: str) -> bool:
        """Bind a reviewed C4 candidate to this checkout's declared branch/base."""
        try:
            current = subprocess.run(
                ["git", "-C", str(self.repo_root), "branch", "--show-current"],
                capture_output=True, text=True, check=False,
            )
            if current.returncode or current.stdout.strip() != branch:
                return False
            head = subprocess.run(
                ["git", "-C", str(self.repo_root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=False,
            )
            if head.returncode:
                return False
            head_sha = head.stdout.strip()
            if base == candidate:
                return False
            for older, newer in ((base, candidate), (candidate, head_sha)):
                result = subprocess.run(
                    ["git", "-C", str(self.repo_root), "merge-base", "--is-ancestor", older, newer],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode:
                    return False
            # A user-facing Release Notes edit is intentionally outside the
            # evidence boundary.  It may remain dirty without invalidating a
            # reviewed candidate; every other dirty path is still fail-closed.
            if not self._only_release_notes_dirty(release_id):
                return False

            # Candidate is the reviewed code snapshot.  A clean, later HEAD
            # is accepted only for the final evidence-only commit; this avoids
            # a self-reference between candidate==HEAD and the QA/Completion
            # artifacts that must name and digest that candidate.  ``--no-
            # renames`` reports both sides of a rename as paths, so moving a
            # code file into the release directory cannot bypass this guard.
            changed = subprocess.run(
                ["git", "-C", str(self.repo_root), "diff", "--name-only", "--no-renames", "-z", f"{candidate}..HEAD"],
                capture_output=True, text=True, check=False,
            )
            if changed.returncode:
                return False
            doc_exact = ("PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md")
            allowed_paths = {f"docs/releases/{release_id}/{name}" for name in doc_exact}
            rel_dir = self._release_rel_path(release_id)
            allowed_paths.update({f"{rel_dir}/{name}" for name in doc_exact})
            for pfx in ("tasks", "ff-tasks"):
                for sub in ("in-progress", "completed", "backlog", ""):
                    base = f"{pfx}/{sub}/{release_id}" if sub else f"{pfx}/{release_id}"
                    allowed_paths.update({f"{base}/{name}" for name in doc_exact})
            return all(path in allowed_paths for path in changed.stdout.split("\0") if path)
        except OSError:
            return False

    def _only_release_notes_dirty(self, release_id: str) -> bool:
        """Accept a clean tree or dirty state limited to this optional document."""
        allowed = {f"docs/releases/{release_id}/RELEASE_NOTES.md"}
        rel_dir = self._release_rel_path(release_id)
        allowed.add(f"{rel_dir}/RELEASE_NOTES.md")
        for pfx in ("tasks", "ff-tasks"):
            for sub in ("in-progress", "completed", "backlog", ""):
                base = f"{pfx}/{sub}/{release_id}" if sub else f"{pfx}/{release_id}"
                allowed.add(f"{base}/RELEASE_NOTES.md")
        try:
            changed = subprocess.run(
                ["git", "-C", str(self.repo_root), "diff", "--name-only", "--no-renames", "-z", "HEAD"],
                capture_output=True, text=True, check=False,
            )
            untracked = subprocess.run(
                ["git", "-C", str(self.repo_root), "ls-files", "--others", "--exclude-standard", "-z"],
                capture_output=True, text=True, check=False,
            )
            if changed.returncode or untracked.returncode:
                return False
            paths = [path for output in (changed.stdout, untracked.stdout) for path in output.split("\0") if path]
            return all(path in allowed for path in paths)
        except OSError:
            return False

    @staticmethod
    def _lifecycle_result(release_id: str, unmet: List[str], tests: Optional[Dict[str, object]]) -> Dict[str, object]:
        unique_unmet = list(dict.fromkeys(unmet))
        next_action = None if not unique_unmet else "Record or correct release artifact evidence: " + unique_unmet[0]
        return {
            "schema_version": 1,
            "ok": not unique_unmet,
            "release_id": release_id,
            "unmet_conditions": unique_unmet,
            "next_action": next_action,
            "strict_tests": tests,
        }
