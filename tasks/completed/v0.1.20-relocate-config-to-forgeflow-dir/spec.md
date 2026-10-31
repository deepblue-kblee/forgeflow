# Functional Specification: Relocate Configuration to .forgeflow/config.json with Update Migration

- **Release ID**: `v0.1.20-relocate-config-to-forgeflow-dir`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`
- **Author**: Antigravity
- **Date**: 2026-10-31
- **Target Component**: `src/forgeflow/scaffold.py`, `src/forgeflow/runner.py`, `src/forgeflow/scanner.py`, `src/forgeflow/diagnostics.py`, `src/forgeflow/cli.py`, `src/forgeflow/_version.py`, `tests/test_scaffold.py`, `tests/test_update_cli.py`, `tests/test_runner.py`, `tests/test_tasks_architecture.py`, `tests/test_cli.py`

## 1. 개요 및 배경 (Overview & Context)

ForgeFlow 셋업 시 프로젝트 루트에 `.forgeflow.json`과 `.forgeflow/` 디렉터리가 동시에 생성되어 루트 디렉터리가 다소 분산되는 구조였다. 루트 디렉터리의 정돈성을 극대화하고 프로젝트 거버넌스 관련 파일들을 `.forgeflow/` 디렉터리 아래로 일원화하기 위해, 프로젝트 설정 파일 경로를 루트 `.forgeflow.json`에서 `.forgeflow/config.json`으로 이전한다.

또한 기존 하위 버전 형태로 구축된 프로젝트(`.forgeflow.json`이 루트에 존재하는 프로젝트)에서 `forgeflow update`를 실행할 경우, 기존 설정을 그대로 보존하면서 최신 규격인 `.forgeflow/config.json`으로 자동 마이그레이션하고 기존 루트 `.forgeflow.json`을 안전하게 정리해야 한다.

아울러 아직 `update`를 수행하지 않은 레거시 프로젝트에서도 `scanner`, `runner`, `diagnostics` 등이 깨지지 않고 자연스럽게 호환(Graceful Fallback) 동작하도록 보장한다.

## 2. 요구사항 및 기능 명세 (Requirements & Specifications)

- **FR-01 (새로운 표준 설정 경로)**:
  - ForgeFlow 설정 파일의 표준 canonical 경로는 `<repo_root>/.forgeflow/config.json`이다.
  - 신규 스캐폴딩(`forgeflow setup`, `scaffold_speckit_hybrid`, `scaffold_repository` 등) 시 `.forgeflow/` 디렉터리 내에 `config.json`을 생성한다.
- **FR-02 (forgeflow update 시 하위 버전 자동 마이그레이션)**:
  - `forgeflow update` 실행 시 대상 저장소에 루트 `.forgeflow.json`이 있고 `.forgeflow/config.json`이 없는 경우(또는 레거시 파일이 잔존하는 경우),
  - 기존 루트 `.forgeflow.json`의 설정을 읽어 사용자 커스텀 설정(예: `governance.tasks_dir`, `governance.test_timeout_seconds`, `governance.auto_create_branch` 등)을 100% 보존하면서 기본 스키마와 딥 머지한다.
  - 새 설정 파일 `<repo_root>/.forgeflow/config.json`으로 저장한다.
  - 기존 루트의 `.forgeflow.json` 파일은 삭제(unlink)하여 최신 레이아웃으로 완전히 전환한다.
  - 마이그레이션된 설정 파일(`.forgeflow/config.json`)을 `updated_files` 목록에 기록한다.
- **FR-03 (투명한 하위 호환 폴백 - Graceful Fallback)**:
  - `scanner.py`, `runner.py`, `diagnostics.py`, `cli.py` 등 설정 파일 조회 로직은 `.forgeflow/config.json`을 최우선 탐색하고, 없을 경우 루트 `.forgeflow.json`을 폴백으로 읽는다.
  - 저장소 루트 감지(`is_repo_root`) 시 `.forgeflow/config.json` 또는 `.forgeflow.json` 중 하나라도 존재하면 정상적인 ForgeFlow 프로젝트로 인식한다.
- **FR-04 (설정 갱신 명령 호환)**:
  - `forgeflow migrate --tasks` 등 설정 파일을 수정하는 CLI 명령은 `.forgeflow/config.json`이 존재하면 해당 파일에 기록하고, 레거시 프로젝트의 경우 폴백 경로에 안전하게 반영한다.
- **FR-05 (Zero-Dependency & Fail-Closed 무결성)**:
  - Python 3.10+ 표준 라이브러리(`json`, `pathlib`, `shutil`, `os`)만 사용한다.
  - 비정상 JSON 형식이나 권한 오류 발생 시 명확한 에러를 발생시킨다.

## 3. 계획된 변경 경로 (Planned Paths)

- `src/forgeflow/_version.py`
- `src/forgeflow/scaffold.py`
- `src/forgeflow/runner.py`
- `src/forgeflow/scanner.py`
- `src/forgeflow/diagnostics.py`
- `src/forgeflow/cli.py`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `docs/spec/CHANGELOG.md`
- `docs/spec/FLOW_SPEC.md`
- `docs/spec/DISTRIBUTION_SPEC.md`
- `tests/test_scaffold.py`
- `tests/test_update_cli.py`
- `tests/test_runner.py`
- `tests/test_tasks_architecture.py`
- `tests/test_cli.py`
- `tasks/in-progress/v0.1.20-relocate-config-to-forgeflow-dir/*`

## 4. 인수 조건 (Acceptance Criteria)

- [x] **AC-01 (신규 스캐폴딩 시 .forgeflow/config.json 생성)**: `scaffold_speckit_hybrid` 및 CLI 셋업 실행 시 `.forgeflow/config.json`이 생성되고 루트에 `.forgeflow.json`이 생성되지 않는다.
- [x] **AC-02 (forgeflow update 시 하위 버전 마이그레이션)**: 루트에 `.forgeflow.json`만 존재하는 하위 버전 프로젝트에서 `forgeflow update`를 실행하면 `.forgeflow/config.json`이 생성되고 루트의 `.forgeflow.json`은 삭제되며, 사용자 커스텀 설정이 그대로 보존된다.
- [x] **AC-03 (하위 호환 폴백 동작)**: `.forgeflow.json`만 존재하는 프로젝트에서도 `runner`의 타임아웃 파싱, `scanner`의 tasks_dir 파싱 및 루트 판별, `diagnostics` 진단이 정상 동작한다.
- [x] **AC-04 (CLI tasks_dir 변경 반영)**: `forgeflow migrate --tasks` 실행 시 최신 프로젝트에서는 `.forgeflow/config.json`의 `tasks_dir`이 정상 갱신된다.
- [x] **AC-05 (회귀 검증 및 테스트 100% 통과)**: 전체 단위 테스트 및 `forgeflow check --all --strict`가 결함 없이 🟢 통과한다.
