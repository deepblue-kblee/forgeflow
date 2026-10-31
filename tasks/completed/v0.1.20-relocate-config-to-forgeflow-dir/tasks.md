# Implementation Tasks: Relocate Configuration to .forgeflow/config.json with Update Migration

- **Release ID**: `v0.1.20-relocate-config-to-forgeflow-dir`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`

## Tasks

- [x] Task 1: `tests/test_scaffold.py` 및 `tests/test_update_cli.py`에 TDD 테스트 케이스 작성 (Red)
  - `scaffold_speckit_hybrid` 시 `.forgeflow/config.json` 생성 검증
  - 구버전 `.forgeflow.json` 보유 시 `update_repo_governance` 실행하면 `.forgeflow/config.json`으로 마이그레이션되고 `.forgeflow.json`이 삭제되는지 검증
  - 사용자 커스텀 설정 키 및 값이 마이그레이션 후 온전히 보존되는지 검증
- [x] Task 2: `src/forgeflow/scaffold.py` 구현 (Green)
  - `_journal_target`에 `.forgeflow/config.json` 허용
  - `scaffold_speckit_hybrid`에서 `.forgeflow/config.json` 생성 및 관리
  - `update_repo_governance`에서 하위 버전 `.forgeflow.json` 자동 감지 및 `.forgeflow/config.json` 마이그레이션 & 구버전 삭제 구현
  - `resolve_auto_create_branch`, `update_tasks_dir_in_config` 등에서 새 경로 및 폴백 지원
- [x] Task 3: `runner.py`, `scanner.py`, `diagnostics.py`, `cli.py` 연동
  - `ReleaseScanner.is_repo_root` 및 `_read_configured_tasks_dir`에서 `.forgeflow/config.json` 지원 (레거시 폴백 유지)
  - `TestRunner._resolve_test_timeout`에서 `.forgeflow/config.json` 지원 (레거시 폴백 유지)
  - `diagnostics.py`에서 `.forgeflow/config.json` 검사 및 안내 문구 업데이트
  - `cli.py` 출력 문구 업데이트
- [x] Task 4: 기존 테스트 스위트 업데이트 및 레거시/신규 호환 테스트 보강
  - `tests/test_scaffold.py`, `tests/test_update_cli.py`, `tests/test_runner.py`, `tests/test_cli.py`, `tests/test_tasks_architecture.py` 등 점검
- [x] Task 5: 규격 문서 및 버전 승격
  - `src/forgeflow/_version.py` 0.1.20으로 승격
  - `CHANGELOG.md` 갱신
  - `FLOW_SPEC.md` 및 `DISTRIBUTION_SPEC.md` 갱신
- [x] Task 6: 전체 단위 테스트 및 하네스 게이트 검증
  - 전체 단위 테스트 100% 통과 확인
  - `forgeflow check --all --strict` 🟢 ALL PASSED 확인
