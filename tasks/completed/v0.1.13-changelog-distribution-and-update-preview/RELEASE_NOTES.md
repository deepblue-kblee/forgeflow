# Release Notes: ForgeFlow v0.1.13

- **Release ID**: `v0.1.13-changelog-distribution-and-update-preview`
- **Release Version**: `v0.1.13`
- **Release Date**: 2026-10-24

---

## 1. 개요 (Overview)

ForgeFlow v0.1.13은 사용자와 AI 에이전트가 배포, 전역 판올림(`forgeflow upgrade`), 로컬 작업 repo 동기화(`forgeflow update`)를 수행했을 때 어떤 거버넌스 사양과 기능이 변경되었는지 직관적으로 인지할 수 있도록 `CHANGELOG.md` 배포 번들링을 강화하고, 업그레이드 및 업데이트 CLI 결과 화면과 JSON 응답에 변경 이력 자동 프리뷰를 제공합니다.

---

## 2. 주요 개선 사항 (Key Improvements)

1. **`forgeflow update` 실행 시 거버넌스 사양 변경 내역(What's Changed) 자동 출력**:
   - `previous_version`에서 `current_version`으로 판올림되면서 도입된 주요 거버넌스 규범 변경 사항을 번들된 `CHANGELOG.md`에서 파싱하여 터미널에 요약 출력.
   - `--json` 모드 응답 객체에 `changelog_summary` 필드를 함께 제공하여, AI 에이전트가 새 거버넌스 규칙을 프롬프트 컨텍스트로 즉각 흡수하도록 지원.
   - 전체 변경 이력 열람 안내(`💡 전체 세부 사양서 열람: 'forgeflow doc show changelog'`) 제공.
2. **`forgeflow upgrade` 완료 시 최신 릴리즈 하이라이트 출력**:
   - 전역 런타임 업그레이드 완료 성공 메시지 하단에, 방금 설치된 신규 버전의 주요 변경점(Highlights: Added, Changed, Fixed)을 터미널에 자동 프리뷰 출력.
   - `--json` 모드 응답 객체에 `release_highlights` 필드 포함.
3. **CHANGELOG 마크다운 추출 엔진 탑재 (`src/forgeflow/scaffold.py`)**:
   - `extract_changelog_section(version)` 및 `extract_changelog_range(prev_ver, curr_ver)` 헬퍼 구현.
   - 번들 템플릿 최우선 참조를 통해 설치 전/후 환경 어디서나 안정적으로 마크다운 섹션 추출 보장.
