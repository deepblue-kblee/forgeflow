# Tasks Checklist: Spec Kit Prerequisite Bundling & Date-Based Amnesia

**Feature Identifier**: `v0.1.1-fix-speckit-prerequisites`  
**Target Release**: `v0.1.1`  
**Created**: 2026-10-20  
**Status**: IN-PROGRESS (Stage 3 ➔ Stage 4)

---

## Phase 1: Setup & Asset Extraction (자산 확보)

- [ ] **Task 1.1**: `src/forgeflow/templates/speckit/scripts/bash/` 디렉토리를 생성하고 공식 6종 스크립트(`check-prerequisites.sh`, `common.sh`, `create-new-feature.sh`, `resolve-template.sh`, `setup-plan.sh`, `setup-tasks.sh`) 파일 배치 및 실행 권한 부여
- [ ] **Task 1.2**: `src/forgeflow/templates/speckit/templates/` 디렉토리를 생성하고 공식 4종 템플릿(`spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`) 파일 배치
- [ ] **Task 1.3**: `pyproject.toml` package-data 설정에 `speckit/**` 패턴 추가 확인

---

## Phase 2: Tests First (TDD 테스트 케이스 작성)

- [ ] **Task 2.1**: `tests/test_hybrid_scaffold.py`에 bash 스크립트 6종 생성 및 실행 권한(`0o755`) 어설션 테스트 추가
- [ ] **Task 2.2**: `tests/test_hybrid_scaffold.py`에 템플릿 4종 생성 및 내용 일치 어설션 테스트 추가
- [ ] **Task 2.3**: `tests/test_hybrid_scaffold.py`에 2026-10-20 이전 레거시 설정 감지 시 v0.1.0 강제 정립 테스트 추가
- [ ] **Task 2.4**: `tests/test_diagnostics.py`에 `doctor` 명령어의 Spec Kit 런타임 검증 테스트 추가

---

## Phase 3: Core Implementation (구현)

- [ ] **Task 3.1**: `src/forgeflow/scaffold.py`의 `scaffold_speckit_hybrid` 메서드 확장:
  - `templates/speckit/scripts/bash/*` 복사 및 `0o755` 권한 부여
  - `templates/speckit/templates/*` 복사
  - 2026-10-20 이전 과거 설정 감지 및 교체 로직 적용
- [ ] **Task 3.2**: `src/forgeflow/diagnostics.py`에 Spec Kit 로컬 전제조건 검증기 추가
- [ ] **Task 3.3**: `forgeflow init --speckit`을 현재 저장소에 실행하여 자체 도그푸딩 완료

---

## Phase 4: Integration Verification & Dogfooding (통합 검증)

- [ ] **Task 4.1**: `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` 실행하여 `exit 0` 및 정상 JSON 페이로드 확인
- [ ] **Task 4.2**: `pytest tests/` 전체 스위트 실행 및 100% Pass 확인
- [ ] **Task 4.3**: `forgeflow check --all --strict` 및 `forgeflow check --stage 2` 실행 확인

---

## Phase 5: Polish & Deployment (배포 준비)

- [ ] **Task 5.1**: `install.sh` 실행하여 로컬 `~/.local/forgeflow/` 패키지 갱신 및 스킬 동기화
- [ ] **Task 5.2**: Gate 2 QA Sign-Off (`QA_SIGNOFF.md`) 생성
- [ ] **Task 5.3**: Gate 3 Release Sign-Off (`RELEASE_SIGNOFF.md`) 완료 및 패키지 밀봉
