# 🏗️ 설계 명세서 (DESIGN.md) - Release {{RELEASE_ID}}

- **릴리즈 식별자**: `{{RELEASE_ID}}`
- **위험도 등급**: **Tier {{TIER}} ({{TIER_NAME}})**
- **Previous ForgeFlow version**: `{{PREVIOUS_FORGEFLOW_VERSION_OR_NA}}` (ForgeFlow self-maintenance only)
- **Target ForgeFlow version**: `{{TARGET_FORGEFLOW_VERSION_OR_NA}}` (ForgeFlow self-maintenance only)
- **Version bump type**: `{{FORGEFLOW_VERSION_BUMP_TYPE_OR_NA}}` (ForgeFlow self-maintenance only)
- **Version change reason**: `{{FORGEFLOW_VERSION_CHANGE_REASON_OR_NA}}` (ForgeFlow self-maintenance only)
- **작성일**: {{DATE}}
- **상태**: Draft (Gate 1 심사 대기)

---

## 1. 아키텍처 개요 (Architecture Overview)

{{ARCHITECTURE_OVERVIEW}}

---

## 2. 모듈 및 인터페이스 설계

### 2.1 컴포넌트 구조
- {{COMPONENT_STRUCTURE}}

### 2.2 I/O 프로토콜 & 에러 핸들링
- {{IO_SPEC}}

---

## 3. 요구사항 추적 매트릭스 (Requirements Traceability Matrix, RTM)

| 요구사항 ID | 설계 컴포넌트 | 테스트 케이스 / 검증 방안 | 상태 |
| :--- | :--- | :--- | :--- |
| **REQ-F01** | `{{MODULE_1}}` | `{{TEST_1}}` | ⏳ Pending |
| **REQ-F02** | `{{MODULE_2}}` | `{{TEST_2}}` | ⏳ Pending |
| **REQ-NF01** | `{{MODULE_3}}` | `{{TEST_3}}` | ⏳ Pending |
| **REQ-NF02** | `{{MODULE_4}}` | `{{TEST_4}}` | ⏳ Pending |

---

## 4. Gate 1 심사 결과 (Gate 1 Review & Verdict)

| 관점 (Perspective) | 심사관 (Reviewer) | 검토 의견 및 리스크 평가 | 판정 (Verdict) |
| :--- | :--- | :--- | :--- |
| **Security & Auth** | {{REVIEWER_SECURITY}} | {{REVIEW_SECURITY_FINDINGS}} | ⏳ Pending |
| **Reliability & Edge Cases** | {{REVIEWER_RELIABILITY}} | {{REVIEW_RELIABILITY_FINDINGS}} | ⏳ Pending |
| **Maintainability & QA** | {{REVIEWER_MAINTAINABILITY}} | {{REVIEW_MAINTAINABILITY_FINDINGS}} | ⏳ Pending |

**Gate 1 Decision**: ⏳ Pending

---

## 5. 조건부 OIDR 전달성 및 픽스처 설계 (Delivery Readiness & Fixture Design)
<!-- OIDR Track active 시 작성 -->
- **Fixture Strategy**: {{FIXTURE_STRATEGY_OR_NA}}
- **Delivery Probe Specification**:
  - Entrypoint: `{{PUBLIC_ENTRYPOINT}}`
  - Non-Mutating Command: `{{PROBE_COMMAND}}`
  - Expected Exit Code: 0
- **Active Target Isolation & Waiver Protocol**: {{WAIVER_PROTOCOL_OR_NA}}

