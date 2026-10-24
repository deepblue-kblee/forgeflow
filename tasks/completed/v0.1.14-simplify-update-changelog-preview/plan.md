# Implementation Plan: v0.1.14-simplify-update-changelog-preview

## 1. 개요 및 아키텍처 접근법 (Architecture Approach)
- `src/forgeflow/scaffold.py`에 마크다운 릴리즈 섹션에서 버전 헤더와 1줄 대표 요약을 추출하는 전용 메서드 `summarize_changelog_section(cls, section: str) -> str`를 구현한다.
- `extract_changelog_range`와 `extract_changelog_section`에 `summary: bool = True` 파라미터를 추가하여, `forgeflow update` 시 호출되는 `changelog_summary`가 자동으로 축약된 1줄 요약 포맷으로 생성되도록 한다.
- 필요 시 전체 섹션 전문 추출(예: `summary=False`)도 지원하여 유연성과 하위 호환성을 유지한다.

## 2. 요약 파싱 알고리즘 설계 (Parsing Algorithm)
1. **버전 헤더 파싱**:
   - `## [0.1.13] - 2026-10-24` -> `[0.1.13] - 2026-10-24` (`## ` 접두사 제거)
2. **대표 요약 라인 파싱**:
   - 버전 헤더 이후의 줄들을 순회하며 빈 줄을 건너뜀.
   - 첫 번째 줄이 `### <title>` 형태인 경우:
     - 만약 `<title>`이 Keep a Changelog 표준 카테고리(`Added`, `Changed`, `Fixed`, `Removed`, `Deprecated`, `Security`, `Added & Improved` 등)가 아니라면, 릴리즈 대표 제목이므로 `f"- {title}"` 형태로 반환 (이모지 포함 보존).
     - 만약 표준 카테고리 헤더라면, 그 다음 줄들에서 첫 번째 불릿 항목(`- **...**` 또는 `- ...`)을 찾아 `f"- {item}"`으로 반환.
   - 불릿이나 서브타이틀이 없는 예외 상황에서는 첫 번째 유의미한 줄을 `- ` 항목으로 포맷팅.
3. **결과 합성**:
   - 단일 버전:
     ```text
     [0.1.13] - 2026-10-24
     - 📢 CHANGELOG 배포 연동 및 upgrade/update 변경 내역 자동 프리뷰 (Changelog Preview & Distribution)
     ```
   - 복수 버전:
     각 버전 요약 블록을 `\n\n`으로 연결.

## 3. 세부 파일 변경 계획
1. `src/forgeflow/scaffold.py`:
   - `summarize_changelog_section(cls, section: str) -> str` 구현
   - `extract_changelog_section(..., summary: bool = False)` 파라미터 지원
   - `extract_changelog_range(..., summary: bool = True)` 기본값 설정
2. `src/forgeflow/_version.py`:
   - `__version__ = "0.1.14"` 로 판올림
3. `src/forgeflow/templates/spec/CHANGELOG.md` & `docs/spec/CHANGELOG.md`:
   - `[0.1.14] - 2026-10-24` 릴리즈 이력 추가
4. `tests/test_update_cli.py`:
   - `test_summarize_changelog_section`: 단일/복수/카테고리형 릴리즈 섹션 요약 정밀 검증 단위 테스트 추가
   - `test_update_includes_changelog_summary`: 축약된 요약 포맷 검증 보강
