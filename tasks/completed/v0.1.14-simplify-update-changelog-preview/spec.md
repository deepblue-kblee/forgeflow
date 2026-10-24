# Feature Specification: v0.1.14-simplify-update-changelog-preview

## 1. 개요 및 배경 (Background & Objectives)
- **배경**: `v0.1.13`에서 `forgeflow update` 실행 시 판올림에 따른 변경 사항(What's Changed)을 터미널에 자동 출력하는 기능이 추가되었으나, `CHANGELOG.md`의 전체 마크다운 섹션(소제목, 카테고리 헤더, 다단계 불릿 등)을 전문 출력하여 터미널 출력이 과도하게 길어지는 불편이 발생함.
- **목적**:
  - `forgeflow update` 실행 시 `changelog_summary`를 릴리즈 헤더와 핵심 제목 한 줄(One-line Summary)로 단순화하여 터미널 가독성을 획기적으로 개선함.
  - 세부 내역은 이미 하단에 안내되고 있는 `forgeflow doc show changelog`를 통해 열람하도록 역할을 명확히 분리함.
  - JSON 응답 객체의 `changelog_summary` 필드에도 간결하게 정리된 요약 텍스트를 제공하여 AI 에이전트의 컨텍스트 토큰을 절감함.

## 2. 사용자 요구사항 및 개선 형식 (User Requirements & Format)
- **현재 형식 (As-Is)**:
  ```text
  ## [0.1.13] - 2026-10-24

  ### 📢 CHANGELOG 배포 연동 및 upgrade/update 변경 내역 자동 프리뷰 (Changelog Preview & Distribution)

  ### Added
  - **`forgeflow update` 실행 시 거버넌스 사양 변경 내역(What's Changed) 자동 출력**:
    - `previous_version`에서 `current_version`으로 판올림되면서 도입된 주요 거버넌스 규범 변경 사항을 번들된 `CHANGELOG.md`에서 파싱하여 터미널에 요약 출력.
    ...
  ```
- **개선 형식 (To-Be)**:
  ```text
  [0.1.13] - 2026-10-24
  - 📢 CHANGELOG 배포 연동 및 upgrade/update 변경 내역 자동 프리뷰 (Changelog Preview & Distribution)
  ```
  - `## ` 마크다운 접두사를 제거한 버전 헤더: `[<version>] - <date>`
  - 릴리즈 대표 제목 또는 대표 변경 요약 한 줄: `- <summary>`
  - 복수 버전 업데이트 시 버전별로 빈 줄 구분하여 순차 출력.

## 3. 계획된 변경 경로 (Planned Paths) - Tier 1
- `src/forgeflow/_version.py`
- `src/forgeflow/scaffold.py`
- `src/forgeflow/cli.py`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `docs/spec/CHANGELOG.md`
- `tests/test_update_cli.py`
- `tasks/in-progress/v0.1.14-simplify-update-changelog-preview/**`

## 4. 인수 조건 (Acceptance Criteria)
- [ ] **AC-1**: `TemplateScaffolder.summarize_changelog_section(section)` (또는 동등한 요약 파서)가 `CHANGELOG.md`의 전체 마크다운 섹션에서 버전 헤더(`[X.Y.Z] - YYYY-MM-DD`)와 대표 타이틀 1줄(`- <title>`)만을 정확히 추출한다.
- [ ] **AC-2**: `extract_changelog_range(prev, curr)`가 버전별 요약 한 줄 포맷으로 결합된 텍스트를 반환하여 `forgeflow update` 실행 시 간결한 변경 내역을 출력한다.
- [ ] **AC-3**: 기존 단위 테스트 297개 및 신규/수정 테스트가 100% Pass해야 하며, `forgeflow check --all --strict`가 결함 없이 🟢 통과해야 한다.
