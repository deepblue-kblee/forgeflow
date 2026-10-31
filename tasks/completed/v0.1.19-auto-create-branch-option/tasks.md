# Implementation Tasks: Support auto_create_branch Governance Configuration

- **Release ID**: `v0.1.19-auto-create-branch-option`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`

## Tasks

- [x] Task 1: `tests/test_scaffold.py` 및 `tests/test_harness.py`에 TDD 실패 테스트 케이스 작성 (Red)
  - `.forgeflow.json` 부재 또는 키 누락 시 `resolve_auto_create_branch`가 `False` 기본값 반환 검증
  - `governance.auto_create_branch: true` 및 `false` 정상 불리언 해석 검증
  - 비불리언(문자열 `"true"`, 숫자 `1` 등) 설정 시 `ValueError` 발생 검증
  - `forgeflow release create` / `task create` 시 `--create-branch` 명시적 플래그 및 기본값 동작 검증
  - `forgeflow lifecycle close` 시 동일 브랜치(분기 생략) 상태에서 안전하게 릴리즈 종료 검증
- [x] Task 2: `src/forgeflow/scaffold.py`에 `resolve_auto_create_branch` 구현 (Green)
  - 엄격한 불리언 타입 검증 및 `False` 기본값 구현
  - 기본 스캐폴드 템플릿의 `.forgeflow.json`에 `"auto_create_branch": false` 스키마 지원
- [x] Task 3: `src/forgeflow/cli.py` 및 `src/forgeflow/harness.py` 연동
  - CLI `release create` / `task create`에 `--create-branch` 플래그 추가
  - `auto_create_branch` 설정 기반 브랜치 생성 건너뛰기 및 현재 브랜치 바인딩 로직 구현
  - `close_release()`에서 비분기 상태의 안전한 Fast-Path 릴리즈 종료 지원
- [x] Task 4: `src/forgeflow/diagnostics.py`에 진단 규칙 연동
  - 유효하지 않은 `auto_create_branch` 설정 검출 및 WARNING 이상 징후 등록
- [x] Task 5: 문서, 템플릿, 스킬 및 버전 승격
  - `FLOW_SPEC.md` 및 `SPECKIT_HOOKS_AND_NORMS.md` 규격 갱신
  - `CHANGELOG.md` 갱신
  - `~/.agents/skills/forgeflow/SKILL.md` 동기화
  - `src/forgeflow/_version.py` 버전 0.1.19 승격
- [x] Task 6: 전체 단위 테스트 및 하네스 게이트 검증
  - 324개 단위 테스트 100% 통과 확인
  - `forgeflow check --stage 2` 및 `forgeflow check --all --strict` 🟢 ALL PASSED 확인
