# Tasks: Changelog Distribution and Upgrade/Update Highlights Preview

- **Release ID**: `v0.1.13-changelog-distribution-and-update-preview`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI UX & Information Architecture)**

---

## 작업 체크리스트 (Atomic Task List)

- [x] **Task 1: Pre-Implementation Gatekeeper Check**
  - `forgeflow check --stage 2` 실행 및 Gate 1 승인 통과 확인

- [x] **Task 2: Implement Changelog Extractors (`src/forgeflow/scaffold.py`)**
  - `find_changelog_file`, `extract_changelog_section`, `extract_changelog_range` 구현
  - `update_repo_governance` 반환 딕셔너리에 `changelog_summary` 필드 주입

- [x] **Task 3: Integrate Changelog Preview in CLI (`src/forgeflow/cli.py`)**
  - `handle_update`: 변경 요약 터미널 출력 및 JSON `changelog_summary` 지원
  - `handle_upgrade`: 설치 완료 후 최신 버전 하이라이트 출력 및 JSON `release_highlights` 지원

- [x] **Task 4: Version Bump & Spec Documentation**
  - `src/forgeflow/_version.py`를 `0.1.13`으로 승격
  - `docs/spec/CHANGELOG.md` 갱신 및 템플릿 동기화

- [x] **Task 5: Unit Tests Synchronization**
  - `tests/test_update_cli.py`: update 시 changelog_summary 반환 및 출력 검증
  - `tests/test_upgrade_cli.py`: upgrade 완료 시 release_highlights 반환 및 출력 검증

- [x] **Task 6: Full Test Suite & Governance Verification**
  - 전체 단위 테스트 100% Pass 확인 (`python3 -m unittest`)
  - 전체 릴리즈 거버넌스 감사 통과 (`forgeflow check --all --strict`)

- [x] **Task 7: QA Sign-Off & Release Seal (Gate 2 & 3)**
  - `QA_SIGNOFF.md` 작성 및 Gate 2 승인
  - `RELEASE_NOTES.md` 작성
  - `RELEASE_SIGNOFF.md` 작성 및 Gate 3 승인
  - `tasks/in-progress/`에서 `tasks/completed/`로 패키지 밀봉/이동
