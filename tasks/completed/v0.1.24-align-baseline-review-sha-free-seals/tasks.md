# Tasks & Implementation Checklist: Align Baseline-Aware Gate 2 with SHA-Free Lifecycle Seals

- **Release ID**: `v0.1.24-align-baseline-review-sha-free-seals`

---

## 1. 구현 태스크 분해 (Atomic Tasks)

- [x] **Task 1: 하네스 Evidence v2 및 밸리데이터의 SHA-Free 정책 지원 (`src/forgeflow/harness.py`)**
  - [x] 1.1: `_parse_evidence_v2`에서 `Binding-Policy` 필드 및 `sha-free` 값 허용
  - [x] 1.2: `_validate_evidence_v2`에서 `Binding-Policy: sha-free` 시 `Base-SHA`, `QA-SHA`, `Reviewer`, `Verification`의 sha-free 완화 검증
  - [x] 1.3: `_validate_v2_package_evidence`에서 `qa_sha` 및 `candidate_sha`가 `sha-free`인 경우의 일치 및 터미널 감사 허용

- [x] **Task 2: 라이프사이클 컨트롤러 및 전이 엔진의 SHA-Free 지원 (`src/forgeflow/lifecycle.py`, `src/forgeflow/harness.py`, `src/forgeflow/cli.py`)**
  - [x] 2.1: `lifecycle.py`: `mark_package_review_pending` 및 `seal_package`에서 `"sha-free"` 허용
  - [x] 2.2: `lifecycle.py`: `completion_ready`에서 `sha-free` 정책 시 `qa_sha_missing`, `candidate_missing` 면제
  - [x] 2.3: `harness.py`: `lifecycle_package_review` 및 `lifecycle_seal`에서 `sha-free` 정책 감지 및 clean worktree 검증 연동
  - [x] 2.4: `cli.py`: `package-review` 및 `seal` 명령어에 `--sha-free` 지원 및 자동 정책 감지

- [x] **Task 3: 공식 명세서 및 템플릿 정비**
  - [x] 3.1: `templates/QA_SIGNOFF.md` 및 `templates/RELEASE_SIGNOFF.md` 최신화
  - [x] 3.2: `src/forgeflow/spec/GATES_AND_LOOPS.md` 및 `docs/spec/GATES_AND_LOOPS.md`에 raw strict vs baseline-aware strict 및 SHA-free 정책 반영
  - [x] 3.3: `src/forgeflow/spec/FLOW_SPEC.md` 및 `docs/spec/FLOW_SPEC.md` 정비

- [x] **Task 4: 테스트 스위트 작성 및 검증**
  - [x] 4.1: `tests/test_lifecycle_harness.py`: SHA-free Evidence v2 검증, `package-review`, `seal`, `audit` 단위 테스트 추가
  - [x] 4.2: `tests/test_lifecycle_cli.py`: CLI `--sha-free` 및 인자 생략 시 자동 감지 테스트 추가
  - [x] 4.3: `tests/test_reviewer.py`: Gate 2 baseline-aware 검토 결과와 SHA-free 라이프사이클 연계 테스트 추가
  - [x] 4.4: 전체 348개 단위 테스트 100% 통과 및 `forgeflow check --all --strict` 전수 검증 통과

- [x] **Task 5: 버전 승격 및 릴리즈 준비**
  - [x] 5.1: `src/forgeflow/_version.py` 버전 `0.1.24` 승격
  - [x] 5.2: `CHANGELOG.md` 및 사양 버전 동기화
