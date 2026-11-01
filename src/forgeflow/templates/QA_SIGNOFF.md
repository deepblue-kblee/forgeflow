# ✅ QA Sign-Off - Release {{RELEASE_ID}}

> 명시적 strict compatibility 템플릿입니다. 기본 workflow에는 필요하지 않습니다. 패키지의 git-sha/sha-free 정책과 실제 evidence를 기록합니다. Package 완료는 Git merge/cleanup을 뜻하지 않으며 operation 권한은 별도입니다.

> Gate 2의 QA Sign-off입니다. 구현 snapshot(`QA-SHA` 또는 SHA-free 무결성)과 자동 검증·기술 review를 승인하며, 최종 release package의 사용자 승인은 Gate 3 `RELEASE_SIGNOFF.md`에서 별도로 기록합니다.

- **릴리즈 식별자**: `{{RELEASE_ID}}`
- **위험도 등급**: **Tier {{TIER}} ({{TIER_NAME}})**
- **심사 일자**: {{DATE}}
- **최종 판정**: **PENDING — 실제 검증 후 판정**

---

## 1. 테스트 실행 및 코드 리뷰 요약

### 1.1 테스트 러너 실행 결과
- **테스트 러너**: Python `unittest` / `pytest`
- **실행 대상**: {{TOTAL_TESTS}}개 테스트
- **결과**: **{{PASSED_TESTS}} Passed / 0 Failed / 0 Error (100% Pass)**

### 1.2 정적 코드 리뷰 정책 (Review Policy)
- **채택 정책**: `raw strict` | `baseline-aware strict` (선택 1)
  - `raw strict`: 선택된 검사 범위의 모든 Warning 0건 (기본 모드: `forgeflow review --strict`)
  - `baseline-aware strict`: Critical 0건 & 신규 Warning 0건 (기준선 모드: `forgeflow review --strict --findings-baseline <ref>`)
- **기준선(Findings Baseline)**: `{{FINDINGS_BASELINE_REF_OR_NONE}}`
- **리뷰 결과 집계**:
  - Critical Findings: `0`
  - Baseline Existing Findings: `{{BASELINE_WARNINGS_OR_ZERO}}`
  - New Findings: `0`
  - Resolved Findings: `{{RESOLVED_WARNINGS_OR_ZERO}}`
  - Modified Scope Warnings (Delta-Zero): `{{MODIFIED_SCOPE_WARNINGS_OR_ZERO}}`

---

## 2. 요구사항 추적 매트릭스 (RTM) 검증 결과

| 요구사항 ID | 명세 요약 | 검증 항목 | 판정 |
| :--- | :--- | :--- | :--- |
| **REQ-F01** | {{REQ_F01_TITLE}} | `{{TEST_1}}` | 🟢 PASS |
| **REQ-F02** | {{REQ_F02_TITLE}} | `{{TEST_2}}` | 🟢 PASS |

---

## 3. Tier 2/3 Checkpoint Ledger (post-policy)

- **정책 버전**: {{CHECKPOINT_POLICY_VERSION_OR_NA}}
- **base SHA / 작업 브랜치 / workspace / clean 상태**: {{BASE_SHA}} / {{TASK_BRANCH}} / {{WORKSPACE}} / {{CLEAN_STATUS}}

| 순서 | record digest | commit SHA | parent SHA | 경계 | 검증 명령·환경 | exit code | 결과 | candidate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| C0 | {{RECORD_DIGEST}} | {{COMMIT_SHA}} | {{PARENT_SHA}} | isolation baseline | {{COMMAND}} | {{EXIT_CODE}} | {{RESULT}} | no |

snapshot, supersession, destructive recovery, 또는 retention decision은 같은 ledger에 append-only로 기록합니다.

---

## 4. 최종 서명

- **QA 리드**: ForgeFlow Automated Gatekeeper
- **상태**: **PENDING**
- **서명 일시**: {{DATE}} KST

---

## 5. 조건부 Consumer Delivery Readiness (소비자 전달성 검증)
<!-- 공용 표면 변경(public-surface-change) 또는 OIDR active 시 작성 -->
- **Consumer Surface Declared**: no <!-- yes | no -->
- **Delivery Target**: {{DELIVERY_TARGET_OR_NA}}
- **Artifact Identity**: {{ARTIFACT_IDENTITY_OR_NA}}
- **Artifact SHA-256 Digest**: {{ARTIFACT_SHA256_OR_NA}}
- **Expected Public Entrypoint**: {{EXPECTED_PUBLIC_ENTRYPOINT_OR_NA}}
- **Clean Consumer Install Verified**: n/a <!-- yes | no | n/a -->
- **Non-Mutating Probe**:
  - Probe Command: {{PROBE_COMMAND_OR_NA}}
  - Exit Code: {{PROBE_EXIT_CODE_OR_NA}}
  - Observable Result: {{PROBE_RESULT_OR_NA}}
- **Active Target Verification**: n/a <!-- verified | waived | n/a -->
- **Waiver Rationale**: {{WAIVER_RATIONALE_OR_NA}} <!-- waived인 경우 필수 -->
- **Live Mutation Authority**: separate <!-- separate | none -->

## ForgeFlow Evidence v2

```text
Schema-Version: 2
Release-ID: {{RELEASE_ID}}
Tier: {{TIER}}
Binding-Policy: git-sha
Task-Branch: PENDING
Base-SHA: PENDING
QA-SHA: PENDING
Stage: PACKAGE_REVIEW_PENDING
Gate-1: PENDING
Gate-2: PENDING
Reviewer: id=security; perspective=Security; verdict=PENDING; qa-sha=PENDING
Reviewer: id=reliability; perspective=Reliability; verdict=PENDING; qa-sha=PENDING
Reviewer: id=maintainability; perspective=Maintainability; verdict=PENDING; qa-sha=PENDING
Verification: id=unit; command=PENDING; result=PENDING; exit-code=PENDING; qa-sha=PENDING
Next-Action: RELEASE_SIGNOFF
```
