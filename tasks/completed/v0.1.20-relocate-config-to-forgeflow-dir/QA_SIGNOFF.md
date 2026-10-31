# Gate 2 QA Sign-off: Relocate Configuration to .forgeflow/config.json with Update Migration

- **Release ID**: `v0.1.20-relocate-config-to-forgeflow-dir`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`
- **QA Sign-off Date**: 2026-10-31
- **Verdict**: `APPROVED`
- **Regression Test Result**: 325 passed in 16.11s (100% Pass)

## 1. 품질 및 테스트 검증 요약

- **신규 스캐폴딩 시 .forgeflow/config.json 생성 검증 (AC-01)**:
  - `test_scaffold_speckit_hybrid_creates_required_files`: `scaffold_speckit_hybrid` 실행 시 `.forgeflow/config.json`이 정상 생성되고 루트의 `.forgeflow.json`은 생성되지 않음을 검증.
  - `test_cli_init_speckit`: CLI `init --speckit` 실행 시 `.forgeflow/config.json`이 정상 생성됨을 확인.
- **forgeflow update 시 하위 버전 마이그레이션 검증 (AC-02)**:
  - `test_update_migrates_legacy_forgeflow_json_to_modern_config`: 루트에 구버전 `.forgeflow.json`만 존재하는 리포지토리에서 `forgeflow update` 실행 시:
    - `.forgeflow/config.json`이 생성되고 최신 버전(`0.1.20`)으로 갱신됨을 확인.
    - 루트의 구버전 `.forgeflow.json` 파일이 안전하게 삭제(unlink)됨을 확인.
    - 사용자 정의 커스텀 거버넌스 설정(`test_timeout_seconds`, `custom_policy`, `custom_root_field`)이 100% 보존됨을 확인.
    - `res["updated_files"]`에 `".forgeflow/config.json"`이 정상 기록됨을 확인.
- **하위 호환 폴백 동작 검증 (AC-03)**:
  - `test_resolve_auto_create_branch_*`: 구버전 `.forgeflow.json` 파일에서도 `resolve_auto_create_branch`가 정상 동작함을 확인.
  - `test_runner.py` 및 `test_scanner.py`: `.forgeflow/config.json`과 `.forgeflow.json` 두 경로 모두에서 타임아웃 및 tasks_dir 설정을 정상 로드함을 확인.
  - `diagnostics.py`: 설정 파일 이상 징후 검출 시 유효한 설정 파일 경로를 안내함을 확인.
- **CLI tasks_dir 변경 반영 검증 (AC-04)**:
  - `test_tasks_architecture.py`: `.forgeflow/config.json`에서 커스텀 `tasks_dir`이 정상 동작함을 검증.
- **전체 단위 및 회귀 테스트 통과 (AC-05)**:
  - 총 325개 단위 테스트 100% 통과 (0 failures, 0 errors).

## 2. 변경 파일 무결성 대조

계획된 변경 경로(Planned Paths)와 실제 변경 파일이 100% 일치함:
- `src/forgeflow/_version.py`
- `src/forgeflow/scaffold.py`
- `src/forgeflow/runner.py`
- `src/forgeflow/scanner.py`
- `src/forgeflow/diagnostics.py`
- `src/forgeflow/cli.py`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `src/forgeflow/templates/spec/FLOW_SPEC.md`
- `src/forgeflow/templates/spec/DISTRIBUTION_SPEC.md`
- `src/forgeflow/templates/spec/SPECKIT_HOOKS_AND_NORMS.md`
- `docs/spec/CHANGELOG.md`
- `docs/spec/FLOW_SPEC.md`
- `docs/spec/DISTRIBUTION_SPEC.md`
- `docs/spec/SPECKIT_HOOKS_AND_NORMS.md`
- `tests/test_scaffold.py`
- `tests/test_update_cli.py`
- `tests/test_hybrid_scaffold.py`
- `tests/test_cli.py`
- `tasks/in-progress/v0.1.20-relocate-config-to-forgeflow-dir/*`
