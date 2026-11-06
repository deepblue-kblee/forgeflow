# Session checkpoint

갱신: 2026-11-06. Base: `main`.

## 현재 상태

- Version: 0.2.1 (`src/forgeflow/_version.py`, `docs/spec/VERSION`)
- Working Tree: clean (`.venv`는 gitignore 대상)
- Archive: tag `archive/pre-0.2.0`, branch `archive/forgeflow-migrate`

## 이번 세션 완료 범위

열린 이슈 #17·#18·#14를 순서대로 처리하고 병합했습니다.

- PR #19 (#17): ForgeFlow workflow 활성화 경계 — 명시 요청 또는 실제 skill 사용 시에만 적용. 단순 commit/push 요청에 workflow·메타데이터 commit 금지.
- PR #20 (#18 P0): workflow 단위 선택·재개·상태 해석 가이드(문서·skill).
- PR #21 (#18 D): `workflow amend` — 동일 workflow agreement 보완, 권한·대상 불변, verification 폐기, 이력 보존.
- PR #22 (#18 E): `workflow list`(active/`--all`), `workflow supersede`, 일반 `workflow stop`/`resume`.
- PR #23 (#18 F·H): `status`/`check`의 machine-readable `interpretation`과 blocker별 구조화 안내.
- PR #24 (#18 G): 외부 commit/push 관찰 연결 검증 및 문서화.
- PR #25 (#14): clean surface·HITL CLI state 검증 보강, cross-branch migration 검증, Python 3.10/3.12 smoke 기록.

## 검증

- `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"` → 239 tests OK
- `python3 scripts/sync-distribution.py --check` → match
- migration tool: `archive/forgeflow-migrate` branch dry-run/apply/idempotency 검증(상세: `docs/session-state/issue-14-verification.md`)
- runtime: Python 3.10.22 / 3.12.16 import·version·HITL smoke 통과

## 남은 작업

1. 릴리스(선택): 동작 변경(#18)을 반영해 version 0.2.2 bump, wheel/sdist build, tag/release 등록.
2. `.venv`가 uv 실행으로 Python 3.12 환경으로 바뀜(필요 시 원복).
3. `dotfiles` 저장소의 전역 에이전트 지침(#17 원칙)은 별도 저장소 작업.

## 미실행

- 실제 타 사용자 account upgrade, 실제 사용자 project migration은 실행하지 않음(격리 시뮬레이션으로 대체).
