# Tasks Checklist: Universal Knowledge Architecture, Graphify Integration, Skills Family & De-SHA Refactoring

- **Release ID**: `v0.1.16-knowledge-system-and-de-sha`
- **Created Date**: 2026-10-27
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane, Scaffolding, Skills & Distribution)**

---

## 작업 체크리스트 (Atomic Task List)

- [x] **Task 1: Pre-Implementation Gatekeeper Check**
  - `PYTHONPATH=src python3 -m forgeflow.cli check --stage 2` 실행 및 Gate 1 통과 확인

- [x] **Task 2: Build 2-Tier Knowledge Architecture & ADRs (Track 1)**
  - `docs/spec/ANTI_PATTERNS.md` 작성 (배경 설명, AP-01~04 요약 테이블)
  - `docs/adr/template.md`, `001-eliminate-git-sha-and-commit-range-bindings.md`, `002-remove-spec-body-hash-binding.md` 작성
  - `src/forgeflow/templates/spec/ANTI_PATTERNS.md` 및 `src/forgeflow/templates/adr/*` 번들링
  - `src/forgeflow/scaffold.py`에 2계층 지식 디렉터리 스캐폴딩 및 업데이트 동기화 반영

- [x] **Task 3: Refactor Harness to Eliminate Brittle Git SHA Checks (Track 4)**
  - `src/forgeflow/harness.py`에서 `_candidate_disallowed_paths` 및 Git Blob 대조기 제거
  - `_has_v2_candidate_binding` 및 `lifecycle_seal`을 실용적 4대 불변식으로 간소화

- [x] **Task 4: Build Official ForgeFlow Agent Skills Family (Track 2 & 3)**
  - `scripts/install-skills.sh`에 `/forgeflow`, `/forgeflow-graphify`, `/setup-forgeflow`, `/update-forgeflow` 스킬 정의 및 설치 로직 반영
  - `install.sh` 스킬 배포 연동 및 실제 `~/.agents/skills/` 설치 확인

- [x] **Task 5: Version Bump & Specification Synchronization**
  - `src/forgeflow/_version.py`를 `0.1.16`으로 승격
  - `docs/spec/CHANGELOG.md` 및 `src/forgeflow/templates/spec/CHANGELOG.md`에 v0.1.16 반영
  - `AGENTS.md` 부팅 시퀀스에 `ANTI_PATTERNS.md` 확인 추가
  - `README.md` 버전 및 신규 스킬 안내 최신화

- [x] **Task 6: Test Suite Synchronization & Full Governance Verification**
  - `tests/test_candidate_seal.py`, `tests/test_lifecycle_harness.py`, `tests/test_scaffold.py` 갱신
  - 전체 단위 테스트 100% Pass 확인 (`python3 -m unittest`)
  - 전체 릴리즈 거버넌스 감사 통과 (`forgeflow check --all --strict`)

- [x] **Task 7: QA Sign-Off & Release Seal (Gate 2 & 3)**
  - `QA_SIGNOFF.md` 작성 및 Tier 3 독립 심사 패널 승인
  - `RELEASE_SIGNOFF.md` 작성 및 Gate 3 승인
  - `tasks/in-progress/`에서 `tasks/completed/`로 패키지 밀봉 및 이동
