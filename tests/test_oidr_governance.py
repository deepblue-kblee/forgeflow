#!/usr/bin/env python3
"""
Unit tests for conditional Operational Incident and Delivery Readiness (OIDR) track.
Covers Issue #20 and Issue #22 requirements:
- Deterministic trigger derivation
- Structured 4-part incident-to-fixture/RTM binding
- Candidate-bound consumer delivery readiness evidence
- Source-checkout leakage protection
- Negative regression tests for all verified gaps
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from forgeflow.validator import DocumentIntegrityValidator, MarkdownSectionParser


class TestOIDRGovernance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def _write_prd(self, content: str):
        path = self.temp_dir / "PRD.md"
        path.write_text(content, encoding="utf-8")
        return path

    def _write_qa(self, content: str):
        path = self.temp_dir / "QA_SIGNOFF.md"
        path.write_text(content, encoding="utf-8")
        return path

    def test_inactive_oidr_track_bypasses_validation_when_no_triggers(self):
        """Standard lean release with no incident/public-surface triggers bypasses OIDR."""
        content = """# PRD
- **OIDR Track**: none
## Requirements
- REQ-F01: internal logic optimization
## Acceptance Criteria
- 1. Internal logic passes tests
"""
        res = MarkdownSectionParser.parse_oidr_prd(content)
        self.assertFalse(res["is_active"])
        self.assertEqual(0, len(res["errors"]))

    # Negative Test 1: Trigger derivation bypass prevention
    def test_qualifying_release_declared_as_oidr_none_fails(self):
        """Release involving incident-fix or public-surface-change cannot declare OIDR Track: none."""
        content = """# PRD
- **릴리즈 식별자**: `v0.21.0-hotfix`
- **OIDR Track**: none
## 1. 배경 및 목적
프로덕션 incident-fix 및 결함 수정을 위한 핫픽스 릴리즈.
## Requirements
- REQ-F01: crash fix
## Acceptance Criteria
- 1. fix crash
"""
        res = MarkdownSectionParser.parse_oidr_prd(content)
        self.assertFalse(res["is_active"])
        self.assertTrue(any("OIDR 트리거 조건" in err and "OIDR Track을 active로 설정해야 합니다" in err for err in res["errors"]))

    # Negative Test 2: Public surface change declared as no consumer surface fails
    def test_public_surface_change_declared_as_no_consumer_surface_fails(self):
        """When PRD declares public-surface-change, QA cannot declare Consumer Surface: no."""
        prd_content = """# PRD
- **OIDR Track**: active
- **Trigger Reason**: public-surface-change
- **Applicability Verdict**: supported
- **External Claim Scope**: CLI interface update
### Incident Brief
- Observed Failure Class: Public CLI flag change
- Safety Boundary: Read only
- Success & Failure Oracles: Exit code 0
Incident-to-Fixture Mapping:
- PROP-01 -> FIXTURE-CLI-HELP -> ORACLE-HELP-TEXT -> REQ-F01
"""
        qa_content = """# QA Sign-off
Status: APPROVED
- **Consumer Surface Declared**: no
"""
        res = MarkdownSectionParser.parse_oidr_qa(qa_content, prd_content=prd_content)
        self.assertTrue(any("Consumer Surface Declared'가 yes가 아닙니다" in err for err in res["errors"]))

    # Negative Test 3: Supported verdict with incomplete 4-part mapping fails
    def test_supported_verdict_with_incomplete_4part_mapping_fails(self):
        """Supported verdict requires PROP-ID -> FIXTURE-ID -> ORACLE-ID -> REQ-ID format."""
        content = """# PRD
- **OIDR Track**: active
- **Trigger Reason**: incident-fix
- **Applicability Verdict**: supported
- **External Claim Scope**: Fix parsing crash
### Incident Brief
- Observed Failure Class: Parser crash on empty bytes
- Safety Boundary: Read-only safe rejection
- Success & Failure Oracles: Return empty struct on empty bytes
Incident-to-Fixture Mapping:
- Empty byte input: `tests/fixtures/empty.bin`
"""
        res = MarkdownSectionParser.parse_oidr_prd(content)
        self.assertTrue(any("4단 정형 구조(PROP-ID -> FIXTURE-ID -> ORACLE-ID -> REQ-ID)를 충족하지 않습니다" in err for err in res["errors"]))

    # Negative Test 4: Supported verdict with duplicate property mapping fails
    def test_supported_verdict_with_duplicate_property_mapping_fails(self):
        """Duplicate property IDs in mapping are rejected."""
        content = """# PRD
- **OIDR Track**: active
- **Trigger Reason**: incident-fix
- **Applicability Verdict**: supported
- **External Claim Scope**: Fix parsing crash
### Incident Brief
- Observed Failure Class: Parser crash
- Safety Boundary: Read-only safe rejection
- Success & Failure Oracles: Return empty struct
Incident-to-Fixture Mapping:
- PROP-01 -> FIXTURE-01 -> ORACLE-01 -> REQ-F01
- PROP-01 -> FIXTURE-02 -> ORACLE-02 -> REQ-F02
"""
        res = MarkdownSectionParser.parse_oidr_prd(content)
        self.assertTrue(any("중복된 Incident Property ID" in err for err in res["errors"]))

    # Negative Test 5: Supported verdict with duplicate fixture mapping fails
    def test_supported_verdict_with_duplicate_fixture_mapping_fails(self):
        """Duplicate fixture IDs in mapping are rejected."""
        content = """# PRD
- **OIDR Track**: active
- **Trigger Reason**: incident-fix
- **Applicability Verdict**: supported
- **External Claim Scope**: Fix parsing crash
### Incident Brief
- Observed Failure Class: Parser crash
- Safety Boundary: Read-only safe rejection
- Success & Failure Oracles: Return empty struct
Incident-to-Fixture Mapping:
- PROP-01 -> FIXTURE-01 -> ORACLE-01 -> REQ-F01
- PROP-02 -> FIXTURE-01 -> ORACLE-02 -> REQ-F02
"""
        res = MarkdownSectionParser.parse_oidr_prd(content)
        self.assertTrue(any("중복된 Fixture ID" in err for err in res["errors"]))

    # Negative Test 6: Missing artifact identity or digest fails
    def test_missing_artifact_identity_or_digest_fails(self):
        """Consumer surface must bind candidate artifact identity and 64-char SHA-256 digest."""
        qa_content = """# QA Sign-off
Status: APPROVED
- **Consumer Surface Declared**: yes
- **Delivery Target**: /opt/forgeflow
- **Expected Public Entrypoint**: forgeflow
- **Clean Consumer Install Verified**: yes
- Probe Command: `forgeflow --version`
- Exit Code: 0
- Observable Result: forgeflow v0.21.0
- **Active Target Verification**: verified
"""
        res = MarkdownSectionParser.parse_oidr_qa(qa_content)
        self.assertTrue(any("Artifact Identity'가 명시되지 않았습니다" in err for err in res["errors"]))
        self.assertTrue(any("Artifact SHA-256 Digest" in err for err in res["errors"]))

    # Negative Test 7: Probe with source-checkout leakage fails
    def test_probe_with_source_checkout_leakage_fails(self):
        """Probe command directly calling src/ or module checkout is rejected as leakage."""
        qa_content = """# QA Sign-off
Status: APPROVED
- **Consumer Surface Declared**: yes
- **Delivery Target**: /opt/forgeflow
- **Expected Public Entrypoint**: forgeflow
- **Artifact Identity**: forgeflow 0.21.0
- **Artifact SHA-256 Digest**: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
- **Clean Consumer Install Verified**: yes
- Probe Command: `python3 -m forgeflow.cli --version`
- Exit Code: 0
- Observable Result: forgeflow v0.21.0
- **Active Target Verification**: verified
"""
        res = MarkdownSectionParser.parse_oidr_qa(qa_content)
        self.assertTrue(any("소스 체크아웃(src/) 또는 직접 모듈 호출을 참조" in err for err in res["errors"]))

    # Negative Test 8: Excluded verdict with resolved claim fails
    def test_excluded_verdict_with_resolved_claim_fails(self):
        content = """# PRD
- **OIDR Track**: active
- **Trigger Reason**: incident-fix
- **Applicability Verdict**: explicitly-excluded
- **External Claim Scope**: This release has resolved the production incident completely.

### Incident Brief
- Observed Failure Class: Large scale network partition
- Safety Boundary: No mutation
- Success & Failure Oracles: Fast rejection
Incident-to-Fixture Mapping:
- N/A: N/A
"""
        res = MarkdownSectionParser.parse_oidr_prd(content)
        self.assertTrue(any("External Claim Scope에 인시던트 해결(resolved)을 주장" in err for err in res["errors"]))

    def test_sanitization_detects_secrets(self):
        content = """# PRD
- **OIDR Track**: active
- **Trigger Reason**: incident-fix
- **Applicability Verdict**: supported

### Incident Brief
- Observed Failure Class: Error with token Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID
- Safety Boundary: none
- Success & Failure Oracles: oracle
"""
        res = MarkdownSectionParser.parse_oidr_prd(content)
        self.assertTrue(any("민감 정보가 감지되었습니다" in err for err in res["errors"]))

    # Positive Test: Valid candidate-bound delivery and 4-part mapping passes
    def test_valid_candidate_bound_delivery_and_4part_mapping_passes(self):
        prd_content = """# PRD
- **릴리즈 식별자**: `v0.21.0-test`
- **위험도 등급**: **Tier 3**
- **OIDR Track**: active
- **Trigger Reason**: public-surface-change
- **Applicability Verdict**: supported
- **External Claim Scope**: Enhanced governance controls and verification
### Incident Brief
- Observed Failure Class: OIDR trigger bypass
- Safety Boundary: Immutable historical releases
- Success & Failure Oracles: Fail-closed on bypass
Incident-to-Fixture Mapping:
- PROP-01 -> FIXTURE-TRIGGER-BYPASS -> ORACLE-FAIL-CLOSED -> REQ-F01
- PROP-02 -> FIXTURE-4PART-BINDING -> ORACLE-EXACT-MATCH -> REQ-F02

## 요구사항
- REQ-F01: Trigger derivation
- REQ-F02: 4-part fixture binding

## 인수 조건
1. All checks pass
"""
        qa_content = """# QA Sign-off
Status: APPROVED
- **Consumer Surface Declared**: yes
- **Delivery Target**: /opt/forgeflow
- **Expected Public Entrypoint**: forgeflow
- **Artifact Identity**: forgeflow 0.21.0
- **Artifact SHA-256 Digest**: 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
- **Clean Consumer Install Verified**: yes
- Probe Command: `forgeflow check --help`
- Exit Code: 0
- Observable Result: usage: forgeflow check
- **Active Target Verification**: waived
- **Waiver Rationale**: External air-gapped target deployment; delivery ready; active target unverified.
"""
        self._write_prd(prd_content)
        self._write_qa(qa_content)

        validator = DocumentIntegrityValidator(self.temp_dir)
        prd_status = validator.validate_file("PRD.md")
        self.assertTrue(prd_status.passed, f"PRD validation failed: {prd_status.errors}")

        qa_status = validator.validate_file("QA_SIGNOFF.md")
        self.assertTrue(qa_status.passed, f"QA validation failed: {qa_status.errors}")


if __name__ == "__main__":
    unittest.main()
