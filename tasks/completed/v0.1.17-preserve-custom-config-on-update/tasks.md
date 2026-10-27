# Implementation Tasks: Preserve Custom Configuration on Update

- **Release ID**: `v0.1.17-preserve-custom-config-on-update`
- **Tier**: `Tier 1 (Minor / Fast-track)`

## Tasks

- [x] Task 1: `src/forgeflow/scaffold.py`에 `deep_merge_config` 헬퍼 메서드 구현 및 `scaffold_speckit_hybrid`, `update_repo_governance` 연동
  - 사용자의 커스텀 key/value 100% 보존
  - 최신 템플릿의 누락된 기본 키 안전 병합
  - 무변경 시 불필요한 덮어쓰기 방지 (no-op check)
- [x] Task 2: `tests/test_update_cli.py`에 커스텀 설정 보존 및 no-op 덮어쓰기 방지 검증 단위 테스트 추가
  - 커스텀 값(`strict_mode: false`, 커스텀 `tasks_dir`, 사용자 최상위 키) 보존 검증
  - 최신 템플릿 새 기본 키 자동 보강 검증
  - 이미 최신 버전이고 변경 없을 때 덮어쓰지 않고 `updated_files`에서 제외되는지 검증
- [x] Task 3: 버전 승격 (`src/forgeflow/_version.py` -> `0.1.17`) 및 CHANGELOG 업데이트
- [x] Task 4: 회귀 테스트 및 `forgeflow check --all --strict` 검증 완료
