# Specification: Fix Doctor False Positive and Avoid Full QA Rebind for Package-Only Changes

- **Release ID**: `v0.1.11-fix-doctor-false-positive-and-qa-rebind`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Diagnostics)**
- **Related Issues**: GitHub Issue #3, GitHub Issue #4

---

## 1. 개요 및 목적 (Overview & Purpose)

본 릴리즈는 진단 엔진(`diagnostics.py`)과 거버넌스 하네스 엔진(`harness.py`)의 신뢰성과 개발 생산성을 향상시키기 위해 GitHub Issue #3과 #4를 통합 해결한다.

1. **Issue #4 (Doctor False Positive)**:
   - `forgeflow update`를 통해 `.forgeflow.json`의 `forgeflow_version`이 최신 버전(예: `0.1.10`)으로 갱신되었을 때, `forgeflow doctor`가 `!= "0.1.0"` 하드코딩 검사로 인해 `LEGACY_CONFIG_DETECTED` 경고를 잘못 발생시키는 오탐을 제거한다.
2. **Issue #3 (Avoid Full QA Rebind for Package-Only Changes)**:
   - Gate 2 통과 후 실제 구현 코드(`src/**`)와 테스트(`tests/**`)가 불변인 상태에서, 패키지 부기(Bookkeeping: `tasks.md` 완료 체크 등) 또는 문서 이동이 발생했을 때 하네스 게이트가 최신 Spec Kit 문서를 인식하지 못해 전체 테스트와 3인 패널 심사를 다시 요구하는 병목을 해소한다.
   - 릴리즈 ID 사전 검증(Preflight)을 통해 사후 패키지 이름 변경 위험을 원천 차단한다.
   - 사양서에 Gate 2(기술적 QA)와 Gate 3(사용자 Go/No-Go)의 역할 경계를 명확히 분리·문서화한다.

---

## 2. 세부 요구사항 (Detailed Requirements)

### 2.1 진단 엔진 오탐 제거 (`src/forgeflow/diagnostics.py`) - Issue #4
- `.forgeflow.json`의 `forgeflow_version` 검사 시, 단순 `!= "0.1.0"` 비교를 지양하고 버전 튜플 비교 또는 레거시 필드 검증을 적용:
  - `parse_version_tuple(forgeflow_version) >= (0, 1, 0)`인 경우 정상 버전으로 인정.
  - 레거시 판정 조건:
    1) `forgeflow_version`이 없거나 `0.1.0` 미만인 경우
    2) 또는 구버전 레거시 필드(`required_documents`, `default_tier` 등)가 `.forgeflow.json` 내에 존재하는 경우
- 이를 통해 `0.1.1` ~ `0.1.11` 등 정상 갱신된 버전 환경에서 `forgeflow doctor` 실행 시 `🟢 HEALTHY`를 정상 반환하도록 개선.

### 2.2 하네스 화이트리스트 확장 (`src/forgeflow/harness.py`) - Issue #3
- `_candidate_disallowed_paths`의 허용 문서 목록(`doc_names`)에 최신 Spec Kit 하이브리드 표준 문서 추가:
  - 기존: `("PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "RELEASE_SIGNOFF.md", "COMPLETION_REPORT.md", "RELEASE_NOTES.md", "ROADMAP.md")`
  - 추가: `"spec.md"`, `"plan.md"`, `"tasks.md"`, `"GATE1_REVIEW.md"`, `"CHANGE_NOTE.md"`, `"checklist.md"`, `"status.md"`
- Gate 2 통과 후 릴리즈 밀봉을 위해 `tasks.md` 완료 체크박스(`[x]`)를 갱신하거나 `CHANGE_NOTE.md`를 추가하더라도 `disallowed`로 판정되지 않도록 보장.

### 2.3 패키지 전용 변경 시 QA 증적 안전 승계 (Verified Package-Only Exemption) - Issue #3
- `git diff --name-only QA-SHA..candidate` 검사 시:
  - 변경된 모든 경로가 허용 문서 목록(`allowed`), 세션 상태(`docs/session-state/**`), 라이프사이클 메타데이터(`.forgeflow/lifecycle/**`)에 속하는 경우,
  - 런타임 코드(`src/**`), 테스트(`tests/**`), 스크립트(`scripts/**`, `.specify/scripts/**`)에 diff가 없음을 검증하고,
  - 기존 QA-SHA의 검증 증적(테스트 결과, 3인 패널 승인)을 승계하여 무의미한 전체 재테스트/재심사를 방지.

### 2.4 릴리즈 ID 사전 검사 (Preflight Release ID Check) - Issue #3
- 스캐폴딩(`scaffold.py`) 및 Stage 1/2 시작 시점(`forgeflow check --stage 2`, `init`)에서 `validate_release_id`를 선제 검증.
- `vX.Y.Z-[a-z0-9-]+` 정규식 규격에 맞지 않는 릴리즈 ID가 작업 디렉토리로 진입하는 것을 초기에 차단하여 사후 이름 변경 마찰을 예방.

### 2.5 사양서 및 거버넌스 가이드 명문화 - Issue #3
- `docs/spec/FLOW_SPEC.md` 및 `docs/spec/GATES_AND_LOOPS.md`에 다음 사항 명시:
  - **Gate 2 (QA Sign-Off)**: 테스트 100% Pass 및 하네스 검증에 따른 "기술적/자동 품질 보증" 단계.
  - **Gate 3 (Release Sign-Off)**: 사용자(인간)의 최종 배포 패키지 검토 및 Go/No-Go 승인 단계.
  - QA-SHA 바인딩의 불변성 원칙과 패키지 메타데이터 전용 변경 시의 안전 승계 규칙 수록.

### 2.6 버전 승격
- `src/forgeflow/_version.py`를 `0.1.11`로 승격.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `forgeflow update`로 `forgeflow_version`이 `0.1.11`로 설정된 저장소에서 `forgeflow doctor` 실행 시 `LEGACY_CONFIG_DETECTED` 오탐 없이 `🟢 HEALTHY`로 진단된다.
- **AC-2**: Gate 2 완료 후 패키지 내 `tasks.md`, `spec.md`, `plan.md`, `CHANGE_NOTE.md` 등의 파일이 수정/추가되어도 `_candidate_disallowed_paths`에서 `disallowed`로 판정되지 않는다.
- **AC-3**: 코드/테스트 경로가 불변인 상태에서 패키지 메타데이터만 갱신되었을 때 QA 바인딩 검증이 성공한다.
- **AC-4**: 유효하지 않은 형식의 릴리즈 ID(`unsafe-id`)로 패키지를 구성하려 할 때 `forgeflow check --stage 2` 등에서 조기 차단된다.
- **AC-5**: `tests/test_diagnostics.py`, `tests/test_candidate_seal.py` 등 관련 단위 테스트가 100% 통과하고 전체 290개 이상의 테스트가 무결하게 동작한다.
- **AC-6**: `forgeflow check --all --strict` 거버넌스 감사가 🟢 ALL PASSED를 달성하고 Tier 3 3인 독립 패널 심사를 완료한다.
