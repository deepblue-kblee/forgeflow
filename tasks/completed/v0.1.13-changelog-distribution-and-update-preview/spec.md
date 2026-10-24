# Specification: Changelog Distribution and Upgrade/Update Highlights Preview

- **Release ID**: `v0.1.13-changelog-distribution-and-update-preview`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI UX & Information Architecture)**

---

## 1. 개요 및 목적 (Overview & Purpose)

사용자가 전역 런타임을 판올림(`forgeflow upgrade`)하거나 작업 repo의 거버넌스 사양을 동기화(`forgeflow update`)할 때, 이번 업데이트에서 프레임워크와 규범이 무엇이 바뀌었는지(What's Changed) 즉각적으로 파악하고 참고할 수 있도록 변경 이력(CHANGELOG) 연계 인터페이스를 도입한다.

1. **`forgeflow upgrade` 완료 후 변경 요약 출력**:
   - 업그레이드 완료 성공 메시지 하단에, 방금 설치된 신규 버전의 주요 변경 사항(Highlights: Added, Changed, Fixed 등)을 자동 프리뷰.
2. **`forgeflow update` 작업 repo 동기화 시 변경점 안내**:
   - `previous_version`에서 `current_version`으로 판올림되면서 도입된 주요 거버넌스 사양 변경 내역을 터미널에 요약 출력.
   - `--json` 모드에서도 `"changelog_summary"` 필드를 반환하여 AI 에이전트가 새 거버넌스 규칙을 프롬프트 컨텍스트로 즉시 흡수하도록 지원.
   - 전체 세부 사양서 열람 안내(`forgeflow doc show changelog`)를 함께 제공.

---

## 2. 세부 요구사항 (Detailed Requirements)

### 2.1 CHANGELOG 섹션 추출 헬퍼 함수 (`src/forgeflow/scaffold.py` 또는 `cli.py`)
- 번들된 공식 사양서 `templates/spec/CHANGELOG.md` 또는 프로젝트 루트의 `docs/spec/CHANGELOG.md`를 탐색.
- 특정 버전(예: `0.1.13`)의 마크다운 섹션(헤더부터 다음 버전 헤더 전까지)을 추출하는 함수 `extract_changelog_section(version: str) -> Optional[str]` 구현.
- 두 버전 범위(`prev_ver` ~ `curr_ver`)에 해당하는 변경 내역을 취합하는 함수 `extract_changelog_range(prev_ver: str, curr_ver: str) -> Optional[str]` 구현.

### 2.2 `forgeflow update` CLI 연동 (`src/forgeflow/cli.py`)
- 작업 repo 거버넌스 갱신 후:
  - `previous_version`과 `current_version`이 다를 경우, 해당 버전 범위의 변경 이력을 요약 출력.
  - `--json` 모드 결과에 `changelog_summary` 필드 포함.
  - 전체 변경 이력 열람 가이드(`💡 전체 세부 사양서 열람: 'forgeflow doc show changelog'`) 출력.

### 2.3 `forgeflow upgrade` CLI 연동 (`src/forgeflow/cli.py`)
- 전역 설치 완료(`installed_version`) 후:
  - 성공 메시지(`🎉 Successfully upgraded ForgeFlow to v{installed_version}!`) 아래에 해당 버전의 CHANGELOG 섹션 요약을 프리뷰 출력.

### 2.4 단위 테스트 동기화
- `tests/test_update_cli.py`: update 완료 시 changelog_summary가 정상 생성되고 출력되는지 검증.
- `tests/test_upgrade_cli.py`: upgrade 완료 시 changelog 요약이 정상 출력되는지 검증.

### 2.5 버전 승격
- `src/forgeflow/_version.py`를 `0.1.13`으로 승격.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `forgeflow update` 실행 시 `previous_version`과 `current_version` 간의 변경 내역 요약과 `forgeflow doc show changelog` 안내가 터미널에 출력된다.
- **AC-2**: `forgeflow update --json` 실행 시 반환된 JSON 객체에 `changelog_summary` 필드가 포함된다.
- **AC-3**: `forgeflow upgrade` 실행 완료 후 신규 버전의 변경 사항 요약이 터미널에 프리뷰된다.
- **AC-4**: 전체 단위 테스트 및 하네스 전수 감사가 100% 통과한다.
- **AC-5**: `src/forgeflow/_version.py`가 `0.1.13`으로 승격된다.
