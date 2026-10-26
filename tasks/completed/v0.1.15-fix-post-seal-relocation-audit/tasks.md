# Tasks Checklist: Allow Committed Completion Relocation in Lifecycle Audit

- **Release ID**: `v0.1.15-fix-post-seal-relocation-audit`
- **Created Date**: 2026-10-26
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Lifecycle Audit)**

---

## 작업 체크리스트 (Atomic Task List)

- [x] **Task 1: Pre-Implementation Gatekeeper Check**
  - `PYTHONPATH=src python3 -m forgeflow.cli check --stage 2` 실행 및 Gate 1 통과 확인

- [x] **Task 2: Implement Byte-Identical Tree Comparison in `harness.py`**
  - `_tree_files_at_commit` 및 `_find_verified_completion_relocation_paths` 구현
  - `_candidate_disallowed_paths`에서 사후 완료 이동 경로 허용 반영
  - `lifecycle_complete`에서 configured tasks 디렉터리 지원 보강

- [x] **Task 3: Version Bump & Spec Documentation**
  - `src/forgeflow/_version.py`를 `0.1.15`로 승격
  - `docs/spec/CHANGELOG.md` 및 `src/forgeflow/templates/spec/CHANGELOG.md`에 v0.1.15 이력 반영

- [x] **Task 4: Add Regression Tests in `test_candidate_seal.py`**
  - 정상 완료 이동 커밋 통과 테스트
  - 변조, 파일 추가, 원본 잔류, 타 릴리즈 이동 차단 테스트
  - 실전 `seal -> complete -> commit -> check_lifecycle_evidence(strict=True)` 전 과정 통과 테스트

- [x] **Task 5: Full Test Suite & Governance Verification**
  - 전체 단위 테스트 100% Pass 확인 (`python3 -m unittest`)
  - 전체 릴리즈 거버넌스 감사 통과 (`forgeflow check --all --strict`)

- [x] **Task 6: QA Sign-Off & Release Seal (Gate 2 & 3)**
  - `QA_SIGNOFF.md` 작성 및 Tier 3 독립 심사 패널 승인
  - `RELEASE_SIGNOFF.md` 작성 및 Gate 3 승인
  - `tasks/in-progress/`에서 `tasks/completed/`로 패키지 밀봉 및 이동
