# Gate 2 QA Sign-off: Preserve Custom Configuration on Update

- **Release ID**: `v0.1.17-preserve-custom-config-on-update`
- **Tier**: `Tier 1 (Minor / Fast-track)`
- **QA Sign-off Date**: 2026-10-27
- **Verdict**: `APPROVED`
- **Regression Test Result**: 306 passed in 14.19s (100% Pass)

## 1. 품질 검증 요약
- **사용자 커스텀 값 보존 검증**:
  - `test_update_preserves_custom_settings_and_keys`: `strict_mode: false`, `max_loop_budget: 12`, 커스텀 `tasks_dir`, 사용자 최상위 메타데이터/플래그가 `forgeflow update` 후 100% 원형 유지됨을 확인.
- **불필요한 덮어쓰기 방지 (No-Op) 검증**:
  - `test_update_no_op_when_already_current_and_customized`: 이미 최신 버전이고 실질적 내용 변경이 없을 때 `.forgeflow.json`을 write하지 않고 `updated_files`에서 안전하게 제외됨을 확인.
- **강제 스캐폴드 안전성 검증**:
  - `test_scaffold_force_preserves_custom_keys`: `scaffold_speckit_hybrid(force=True)` 직접 호출 시에도 사용자 커스텀 키가 유실되지 않음을 확인.
- **신규 기본값 보강 검증**:
  - `test_deep_merge_config_populates_missing_defaults_without_overwriting`: 누락된 기본 설정 키만 안전하게 재귀적으로 채워지고 기존 값은 덮어쓰지 않음을 확인.

## 2. 변경 파일 무결성 대조
- 계획된 경로와 실제 변경 경로 100% 일치:
  - `src/forgeflow/_version.py`
  - `src/forgeflow/scaffold.py`
  - `tests/test_update_cli.py`
  - `docs/spec/CHANGELOG.md`
  - `src/forgeflow/templates/spec/CHANGELOG.md`
  - `tasks/in-progress/v0.1.17-preserve-custom-config-on-update/*`
