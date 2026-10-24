# Implementation Plan: Fix Doctor False Positive and Avoid Full QA Rebind for Package-Only Changes

- **Release ID**: `v0.1.11-fix-doctor-false-positive-and-qa-rebind`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Diagnostics)**

---

## 1. 아키텍처 및 세부 설계 (Architecture & Design)

### 1.1 진단 엔진 오탐 제거 (`src/forgeflow/diagnostics.py`)
- **현재 결함**: `cfg.get("forgeflow_version") != "0.1.0"`으로 하드코딩되어 `0.1.1` 이상의 최신 버전이 레거시로 오인됨.
- **설계**:
  - `parse_version_tuple`을 활용하여 버전 튜플 비교 도입.
  - 판별 규칙:
    - `forgeflow_version`이 유효한 버전 튜플 `(>= (0, 1, 0))`이고, 구버전 잔재 필드(`required_documents`, `default_tier` 등)가 없으면 정상.
    - `v_tuple < (0, 1, 0)`이거나 구버전 잔재 필드가 존재하는 경우에만 `LEGACY_CONFIG_DETECTED` 발생.

### 1.2 하네스 화이트리스트 확장 및 패키지 전용 변경 검증 (`src/forgeflow/harness.py`)
- **현재 결함**: `doc_names`에 2026-10-20 이전 산출물 이름만 등록되어 있어 최신 `spec.md`, `plan.md`, `tasks.md`, `GATE1_REVIEW.md`, `CHANGE_NOTE.md` 수정 시 `disallowed` 판정.
- **설계**:
  - `doc_names` 튜플에 최신 Spec Kit 하이브리드 표준 문서 추가:
    `("spec.md", "plan.md", "tasks.md", "GATE1_REVIEW.md", "QA_SIGNOFF.md", "RELEASE_SIGNOFF.md", "RELEASE_NOTES.md", "CHANGE_NOTE.md", "checklist.md", "status.md", "PRD.md", "DESIGN.md", "COMPLETION_REPORT.md", "ROADMAP.md")`
  - `_candidate_disallowed_paths`에서 `allowed` 집합 구성 시 위 문서들을 모두 포함.
  - 패키지 디렉토리 내의 마크다운 문서 및 메타데이터, `docs/session-state/`, `.forgeflow/lifecycle/` 파일만 변경된 경우 `disallowed` 목록에 등록되지 않음을 보장.

### 1.3 릴리즈 ID 사전 검증 (Preflight Validation)
- `src/forgeflow/cli.py` (`verify_stage2_gatekeeper`):
  - `tasks/in-progress/`에 진입한 패키지의 `release_id`에 대해 `validate_release_id(pkg.name)`를 사전 실행.
  - 유효하지 않은 릴리즈 ID가 있는 경우 Gate 2 통과 전인 Stage 2 시점에서 조기 fail-closed 에러를 발생시켜 사후 디렉토리 변경을 원천 예방.

### 1.4 사양서 및 템플릿 명문화
- `docs/spec/FLOW_SPEC.md` 및 `docs/spec/GATES_AND_LOOPS.md`:
  - Gate 2 (기술적 QA 서명: 테스트 통과 및 하네스 검증에 따른 에이전트/QA 자동 승인)와 Gate 3 (사용자 최종 패키지 Go/No-Go 승인)의 역할 분리를 명문화.

### 1.5 버전 승격
- `src/forgeflow/_version.py`를 `0.1.11`로 승격.

---

## 2. 변경 파일 목록 (Target Files)
1. `src/forgeflow/diagnostics.py`: 레거시 설정 진단 로직 교정
2. `src/forgeflow/harness.py`: `_candidate_disallowed_paths` 화이트리스트 확장
3. `src/forgeflow/cli.py`: `verify_stage2_gatekeeper` 릴리즈 ID 조기 검증 추가
4. `src/forgeflow/_version.py`: 버전 `0.1.11` 승격
5. `docs/spec/FLOW_SPEC.md`, `docs/spec/GATES_AND_LOOPS.md`, `docs/spec/CHANGELOG.md`: 사양 및 이력 문서 갱신
6. `src/forgeflow/templates/spec/*`: 템플릿 동기화
7. `tests/test_diagnostics.py`, `tests/test_candidate_seal.py`: 단위 테스트 추가 및 검증

---

## 3. 검증 전략 (Verification Strategy)
- 단위 테스트 실행: `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"`
- 하네스 거버넌스 감사: `forgeflow check --all --strict`
- Gate 2 QA 승인 및 Gate 3 릴리즈 승인 완료 후 밀봉
