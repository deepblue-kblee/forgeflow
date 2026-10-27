# Technical Plan: Preserve Custom Configuration on Update

- **Release ID**: `v0.1.17-preserve-custom-config-on-update`
- **Tier**: `Tier 1 (Minor / Fast-track)`

## 1. 아키텍처 및 설계 원칙

### 1.1 Deep Merge with User Precedence
기존 설정(`existing`)과 최신 기본 템플릿(`defaults`)을 재귀적으로 병합하는 알고리즘을 구현한다.
- 딕셔너리 키 탐색:
  - `defaults`에 있는 키가 `existing`에 없으면 `defaults`의 값을 추가한다.
  - `existing`에 이미 존재하는 키는 사용자의 값을 100% 우선 보존한다 (단, 중첩 딕셔너리의 경우 재귀적으로 병합).
  - `existing`에만 있는 사용자 커스텀 최상위/하위 키는 그대로 보존한다.
  - `forgeflow_version`은 최신 런타임 버전(`__version__`)으로 갱신한다.

### 1.2 무변경 덮어쓰기 방지 (No-Op Preservation)
- `update_repo_governance` 실행 시:
  - 병합 결과(`merged_config`)가 기존 파일 내용과 완벽히 동일하다면(`merged_config == existing_config`), 불필요한 디스크 쓰기(`config_file.write_text`)를 생략한다.
  - `updated_files` 목록에서도 `.forgeflow.json`을 제외한다.
  - 버전이 변경되었거나 새 키가 추가/보강된 경우에만 원자적으로 저장하고 `updated_files`에 포함한다.

### 1.3 `scaffold_speckit_hybrid` 안전성 보강
- `scaffold_speckit_hybrid`의 `force=True` 시에도 `existing`의 사용자 커스텀 키를 임의로 버리지 않고 병합하여 파일 덮어쓰기 도중 데이터 유실이 발생하지 않도록 방어한다.
