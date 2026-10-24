# Release Notes: v0.1.14

## 릴리즈 개요
`v0.1.14`는 `forgeflow update` 명령어 실행 시 터미널과 JSON에 출력되는 거버넌스 사양 변경 내역(`changelog_summary`)을 마크다운 전문 대신 간결한 버전 헤더와 1줄 대표 요약 포맷으로 단순화하여 터미널 가독성과 토큰 효율성을 크게 향상시켰습니다.

## 주요 변경 사항
1. **`forgeflow update`의 `changelog_summary` 출력 간결화**:
   - `CHANGELOG.md` 전문 대신 버전 헤더(`[<version>] - <date>`)와 대표 타이틀 1줄(`- <title>`)만 출력하도록 간소화.
   - 다중 버전 판올림 시 버전별 1줄 요약 블록을 순차 출력하고, 전체 변경 이력은 기존과 동일하게 `forgeflow doc show changelog`로 안내.
2. **CHANGELOG 1줄 요약 추출 엔진 (`TemplateScaffolder.summarize_changelog_section`) 탑재**:
   - 릴리즈 마크다운 섹션에서 대표 타이틀 또는 첫 번째 핵심 불릿을 감지하여 안전하게 1줄 요약으로 정제.
   - `extract_changelog_range(..., summary=True)` 기본값 연동.
3. **단위 테스트 및 거버넌스 무결성**:
   - 신규 단위 테스트 추가 및 전체 298개 테스트 100% 통과.
