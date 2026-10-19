# 📋 PRD (Product Requirements Document) - Release {{RELEASE_ID}}

- **릴리즈 식별자**: `{{RELEASE_ID}}`
- **위험도 등급**: **Tier {{TIER}} ({{TIER_NAME}})**
- **Previous ForgeFlow version**: `{{PREVIOUS_FORGEFLOW_VERSION_OR_NA}}` (ForgeFlow self-maintenance only)
- **Target ForgeFlow version**: `{{TARGET_FORGEFLOW_VERSION_OR_NA}}` (ForgeFlow self-maintenance only)
- **Version bump type**: `{{FORGEFLOW_VERSION_BUMP_TYPE_OR_NA}}` (ForgeFlow self-maintenance only)
- **Version change reason**: `{{FORGEFLOW_VERSION_CHANGE_REASON_OR_NA}}` (ForgeFlow self-maintenance only)
- **작성일**: {{DATE}}
- **상태**: Draft (Gate 1 심사 대기)

---

## 1. 배경 및 목적 (Background & Objectives)

### 1.1 배경
- {{BACKGROUND_SUMMARY}}

### 1.2 목적
1. {{OBJECTIVE_1}}
2. {{OBJECTIVE_2}}

---

## 2. 기능 요구사항 (Functional Requirements)

### REQ-F01: {{FEATURE_TITLE_1}}
- {{FEATURE_SPEC_1}}

### REQ-F02: {{FEATURE_TITLE_2}}
- {{FEATURE_SPEC_2}}

---

## 3. 비기능 요구사항 (Non-Functional Requirements)

### REQ-NF01: {{NON_FUNC_TITLE_1}}
- {{NON_FUNC_SPEC_1}}

### REQ-NF02: {{NON_FUNC_TITLE_2}}
- {{NON_FUNC_SPEC_2}}

---

## 4. 인수 조건 (Acceptance Criteria)

1. {{CRITERIA_1}}
2. {{CRITERIA_2}}
3. 전체 단위/통합 회귀 테스트 스위트 100% Pass 및 `harness check --strict` 게이트 통과.

---

## 5. 조건부 OIDR 트랙 (Operational Incident and Delivery Readiness)
<!-- 인시던트 해결(incident-fix), 공용 표면 변경(public-surface-change), 운영 해결 클레임(operational-claim) 릴리즈 시 필수 활성화 -->
- **OIDR Track**: none <!-- active | none -->
- **Trigger Reason**: n/a <!-- incident-fix | public-surface-change | operational-claim | n/a -->
- **Applicability Verdict**: n/a <!-- supported | explicitly-excluded | discovery-only | n/a -->
- **External Claim Scope**: {{EXTERNAL_CLAIM_SCOPE_OR_NA}}

### Incident Brief (OIDR Track active 시 필수)
- Observed Failure Class: {{OBSERVED_FAILURE_CLASS_OR_NA}}
- Safety Boundary: {{SAFETY_BOUNDARY_OR_NA}}
- Success & Failure Oracles: {{SUCCESS_AND_FAILURE_ORACLES_OR_NA}}
- Incident-to-Fixture Mapping:
  - PROP-{{PROPERTY_ID}} -> FIXTURE-{{FIXTURE_ID}} -> ORACLE-{{ORACLE_ID}} -> REQ-{{REQ_ID}}

