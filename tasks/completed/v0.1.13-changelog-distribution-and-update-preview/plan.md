# Implementation Plan: Changelog Distribution and Upgrade/Update Highlights Preview

- **Release ID**: `v0.1.13-changelog-distribution-and-update-preview`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI UX & Information Architecture)**

---

## 1. 아키텍처 및 세부 설계 (Architecture & Design)

### 1.1 CHANGELOG 섹션 추출 엔진 (`src/forgeflow/scaffold.py`)
- **CHANGELOG 파일 탐색 우선순위**:
  1. `Path.home() / ".local" / "forgeflow" / "current" / "lib" / "forgeflow" / "templates" / "spec" / "CHANGELOG.md"` (전역 설치 환경)
  2. `HierarchicalRootScanner.find_root() / "docs" / "spec" / "CHANGELOG.md"` (개발 저장소 환경)
  3. `HierarchicalRootScanner.find_root() / "src" / "forgeflow" / "templates" / "spec" / "CHANGELOG.md"` (내장 템플릿 환경)
- **추출 헬퍼 함수**:
  - `extract_changelog_section(version: str) -> Optional[str]`:
    - 정규식 `(?ms)^##\s*\[\s*{re.escape(version)}\s*\].*?(?=^##\s*\[|\Z)`를 통해 특정 버전 섹션 추출.
  - `extract_changelog_range(prev_version: str, curr_version: str) -> Optional[str]`:
    - `parse_version_tuple(prev_version) < v_tuple <= parse_version_tuple(curr_version)`에 해당하는 모든 버전 섹션을 취합하여 변경 요약 생성.

### 1.2 `update_repo_governance` 및 `handle_update` 연동
- `update_repo_governance(root: Path)`:
  - `previous_version`과 `current_version` 간의 `changelog_summary`를 생성하여 결과 딕셔너리에 포함.
- `handle_update(args)`:
  - 비대화형/JSON 모드: JSON payload에 `"changelog_summary"` 필드 포함.
  - 터미널 모드:
    ```text
    📦 ForgeFlow Governance Updated: v{prev} ➔ v{curr}
    ------------------------------------------------------------
    📋 What's Changed in this update:
    {changelog_summary}
    ------------------------------------------------------------
    💡 전체 세부 사양서 열람: 'forgeflow doc show changelog'
    ```

### 1.3 `handle_upgrade` 연동
- 전역 설치 완료 후:
  - `extract_changelog_section(installed_version)` 호출.
  - 터미널 모드:
    ```text
    🎉 Successfully upgraded ForgeFlow to v{installed_version}!

    📋 Release Highlights for v{installed_version}:
    {highlights}
    ------------------------------------------------------------
    💡 전체 세부 사양서 열람: 'forgeflow doc show changelog'
    ```
  - `--json` 모드: JSON payload에 `"release_highlights"` 필드 포함.

### 1.4 버전 승격
- `src/forgeflow/_version.py`를 `0.1.13`으로 승격.

---

## 2. 변경 파일 목록 (Target Files)
1. `src/forgeflow/scaffold.py`: CHANGELOG 추출 헬퍼 함수 및 `update_repo_governance` 연동
2. `src/forgeflow/cli.py`: `handle_upgrade`, `handle_update` 출력 보강
3. `src/forgeflow/_version.py`: 버전 `0.1.13` 승격
4. `docs/spec/CHANGELOG.md`, `src/forgeflow/templates/spec/CHANGELOG.md`: 이력 동기화
5. `tests/test_update_cli.py`, `tests/test_upgrade_cli.py`: 단위 테스트 추가 및 검증

---

## 3. 검증 전략 (Verification Strategy)
- 단위 테스트 실행: `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"`
- 하네스 거버넌스 감사: `forgeflow check --all --strict`
- Gate 2 QA 승인 및 Gate 3 릴리즈 승인 완료 후 밀봉
