# Session checkpoint

갱신: 2026-11-07. Base: `main`.

## 현재 상태

- Version: 0.2.2 (`src/forgeflow/_version.py`, `docs/spec/VERSION`)
- Git Tag: `v0.2.2` (merge commit `2d98d6f`)
- GitHub Release: `v0.2.2` 등록 완료
- Working Tree: clean (`.venv`는 gitignore 대상)
- Archive: tag `archive/pre-0.2.0`, branch `archive/forgeflow-migrate`

## 완료 범위

열린 이슈 #17·#18·#14를 처리하고 v0.2.2로 릴리스했습니다.

- #17: workflow 활성화 경계 — 명시 요청 또는 실제 skill 사용 시에만 시작, 단순 commit/push 요청에 workflow·메타데이터 commit 금지.
- #18 P0: workflow 단위 선택·재개·상태 해석 가이드.
- #18 D: `workflow amend` — agreement 보완, 권한·대상 불변, verification 폐기.
- #18 E: `workflow list`/`supersede`, 일반 `stop`/`resume`.
- #18 F·H: `status`/`check`의 interpretation과 blocker 구조화 안내.
- #18 G: 외부 commit/push 관찰 연결 검증·문서화.
- #14: clean surface·HITL CLI state 검증 보강, cross-branch migration·Python 3.10/3.12 검증 기록.

## 배포판 현황

- Local Artifacts: `dist/forgeflow-0.2.2-py3-none-any.whl`, `dist/forgeflow-0.2.2.tar.gz`
- 격리 설치 검증: Python 3.12 wheel, Python 3.10 sdist — `forgeflow version` = 0.2.2, spec VERSION = 0.2.2, legacy module 미포함

## 검증

- `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"` → 239 tests OK
- `python3 scripts/sync-distribution.py --check` → match
- 상세 #14 결과: `docs/session-state/issue-14-verification.md`

## 남은 작업

1. 활성 사용자 배포(`~/.local/share/forgeflow/current`)를 v0.2.2로 upgrade할지 결정.
2. `dotfiles` 저장소의 전역 에이전트 지침(#17 원칙)은 별도 저장소 작업.
3. 실제 사용자 project migration은 미실행(격리 검증으로 대체).

## 미실행

- 실제 타 사용자 account upgrade, 실제 사용자 project migration.
