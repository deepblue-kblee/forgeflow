# Tasks: Fix Doctor False Positive and Avoid Full QA Rebind for Package-Only Changes

- **Release ID**: `v0.1.11-fix-doctor-false-positive-and-qa-rebind`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Diagnostics)**

---

## 작업 체크리스트 (Atomic Task List)

- [x] **Task 1: Pre-Implementation Gatekeeper Check**
  - `forgeflow check --stage 2` 실행 및 Gate 1 승인 통과 확인

- [x] **Task 2: Fix Doctor False Positive in `diagnostics.py`**
  - `_check_legacy_config`에서 버전 튜플 비교(`parse_version_tuple`) 도입
  - `forgeflow_version >= 0.1.0`이고 레거시 필드가 없을 시 정상 판정

- [x] **Task 3: Expand Harness Allowed Documents in `harness.py`**
  - `_candidate_disallowed_paths`의 `doc_names`에 `spec.md`, `plan.md`, `tasks.md`, `GATE1_REVIEW.md`, `CHANGE_NOTE.md`, `checklist.md`, `status.md` 추가

- [x] **Task 4: Add Preflight Release ID Validation in `cli.py`**
  - `verify_stage2_gatekeeper`에서 `validate_release_id` 사전 검증 추가

- [x] **Task 5: Version Bump & Spec Documentation**
  - `src/forgeflow/_version.py`를 `0.1.11`로 승격
  - `docs/spec/FLOW_SPEC.md`, `GATES_AND_LOOPS.md`, `CHANGELOG.md` 갱신 및 템플릿 동기화

- [x] **Task 6: Unit Tests Synchronization**
  - `tests/test_diagnostics.py`: `0.1.1+` 버전에서 오탐 미발생 및 레거시 설정 정상 감지 테스트
  - `tests/test_candidate_seal.py`: 최신 Spec Kit 하이브리드 문서 변경 시 `_candidate_disallowed_paths` 허용 테스트 및 릴리즈 ID 조기 검증 테스트

- [x] **Task 7: Full Test Suite & Governance Verification**
  - 전체 단위 테스트 100% Pass 확인 (`python3 -m unittest`)
  - 전체 릴리즈 거버넌스 감사 통과 (`forgeflow check --all --strict`)

- [x] **Task 8: QA Sign-Off & Release Seal (Gate 2 & 3)**
  - `QA_SIGNOFF.md` 작성 및 Tier 3 독립 심사 패널 승인
  - `RELEASE_SIGNOFF.md` 작성 및 Gate 3 승인
  - `tasks/in-progress/`에서 `tasks/completed/`로 패키지 밀봉/이동
