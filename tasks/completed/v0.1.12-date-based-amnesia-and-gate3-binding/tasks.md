# Tasks: Date-Based Amnesia Verification and Gate 3 Final Single-Binding

- **Release ID**: `v0.1.12-date-based-amnesia-and-gate3-binding`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Diagnostics)**

---

## 작업 체크리스트 (Atomic Task List)

- [x] **Task 1: Pre-Implementation Gatekeeper Check**
  - `forgeflow check --stage 2` 실행 및 Gate 1 승인 통과 확인

- [x] **Task 2: Enhance Date-Based Amnesia in `diagnostics.py`**
  - 기준일(2026-10-20) 타임스탬프 및 Spec Kit 하이브리드 구조(`.specify/memory/constitution.md`) 교차 판별 로직 구현
  - 과거 0.22.x/0.23.0 레거시 설정 감지 및 미래 0.22.x+ 최신 설정 정상 허용 분기 구현

- [x] **Task 3: Version Bump & Spec Documentation**
  - `src/forgeflow/_version.py`를 `0.1.12`로 승격
  - `docs/spec/FLOW_SPEC.md`, `GATES_AND_LOOPS.md`, `CHANGELOG.md` 갱신 및 템플릿 동기화

- [x] **Task 4: Unit Tests Synchronization (`tests/test_diagnostics.py`)**
  - 과거 0.22.1 레거시 설정 감지 테스트
  - 미래 0.22.0+ 최신 정상 설정 통과 테스트
  - Spec Kit 부재 및 구버전 필드 감지 테스트

- [x] **Task 5: Full Test Suite & Governance Verification**
  - 전체 단위 테스트 100% Pass 확인 (`python3 -m unittest`)
  - 전체 릴리즈 거버넌스 감사 통과 (`forgeflow check --all --strict`)

- [x] **Task 6: QA Sign-Off & Release Seal (Gate 2 & 3)**
  - `QA_SIGNOFF.md` 작성 및 Tier 3 독립 심사 패널 승인
  - `RELEASE_SIGNOFF.md` 작성 및 Gate 3 승인
  - `tasks/in-progress/`에서 `tasks/completed/`로 패키지 밀봉/이동
