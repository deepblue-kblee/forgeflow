# Tasks Checklist: v0.1.14-simplify-update-changelog-preview

- [x] **Task 1.0**: 단위 테스트 작성 (TDD)
  - [x] `tests/test_update_cli.py`에 `summarize_changelog_section` 검증 및 `extract_changelog_range(..., summary=True)` 단위 테스트 추가
- [x] **Task 2.0**: CHANGELOG 요약 엔진 구현
  - [x] `src/forgeflow/scaffold.py`에 `summarize_changelog_section` 구현
  - [x] `extract_changelog_section` 및 `extract_changelog_range`에 `summary` 파라미터 연동
  - [x] `src/forgeflow/_version.py` 버전 `0.1.14`로 승격
- [x] **Task 3.0**: CHANGELOG 및 사양 문서 갱신
  - [x] `docs/spec/CHANGELOG.md` 및 `src/forgeflow/templates/spec/CHANGELOG.md`에 v0.1.14 항목 반영
- [x] **Task 4.0**: 전체 테스트 스위트 및 거버넌스 감사 실행
  - [x] `.venv/bin/pytest` 100% Pass 검증 (298 passed)
  - [x] `forgeflow check --all --strict` 🟢 ALL PASSED 검증
- [x] **Task 5.0**: Gate 2 QA Sign-Off 및 Gate 3 릴리즈 밀봉
  - [x] `QA_SIGNOFF.md` 작성 및 Gate 2 승인
  - [x] `RELEASE_SIGNOFF.md` 및 `RELEASE_NOTES.md` 작성
  - [x] `forgeflow lifecycle seal` 및 `forgeflow lifecycle complete` 완료
