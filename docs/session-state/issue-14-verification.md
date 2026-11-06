# Issue #14 검증 matrix

대상: ForgeFlow 0.2.0/0.2.1의 HITL, clean init, user-project migration, 다른 account upgrade, runtime 호환성.

## 검증 결과

| 영역 | 검증 수단 | 결과 |
| --- | --- | --- |
| 1. Design checkpoint HITL | `tests/test_workflow_hitl.py`(auto/continue/revise/stop) + `tests/test_workflow_cli_contract.py::test_hitl_design_checkpoint_cli_json_state` | 통과. `check`가 `awaiting-user`/exit 3을 반환하고 JSON state의 checkpoint summary/decision/note가 CLI 결과와 일치 |
| 2. Clean init와 제거된 legacy surface | `tests/test_clean_surface.py` | 통과. `release`/`lifecycle`/`migrate`/`task`/`check` CLI 미노출, `lifecycle.py`·`harness.py`·`migration.py`·`legacy_assets.py` 모듈 미포함, `init`이 `tasks/` 미생성 |
| 3. User-project migration tool | `archive/forgeflow-migrate` branch `tests/test_migration.py`(11) + v0.1.24 fixture에 `forgeflow-migrate.py` dry-run/apply 수동 검증 | 통과. archive tag 생성, `tasks/`·`docs/releases/`·strict 자산 제거, 0.2.x config 생성, AGENTS.md 보존, 재실행 시 tag 존재 가드 |
| 4. 다른 account upgrade | `tests/test_upgrade_integration.py`, `tests/test_distribution.py`(격리 HOME/prefix/bin/skills) | 통과(격리 시뮬레이션). 실제 타 account 설치는 미실행 |
| 5. Runtime 호환성 | `uv run --python 3.10/3.12`에서 import·version·HITL smoke | 통과. 3.10.22, 3.12.16 |

## 공통 gate

- `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"` → 235 tests OK
- `python3 scripts/sync-distribution.py --check` → match

## M05/M06/M07/U06 매핑

`next-actions.md`의 M05/M06/M07/U06은 닫힌 #12의 update/upgrade matrix ID입니다.

- M05(완료된 strict package·과거 docs/releases·readiness-only task): `tests/test_update_cli.py`, `tests/test_upgrade_integration.py`
- M06(managed spec link·user directory·symlink parent): `tests/test_distribution.py`, `tests/test_hybrid_scaffold.py`
- M07(Spec Kit 미사용·명시 strict·host-owned): `tests/test_hybrid_scaffold.py::test_default_init_does_not_inject_strict_bundle_or_speckit`, `test_host_owner_disables_auto_branch_even_when_legacy_setting_is_true`
- U06(exact-key rollback·legacy rollback·retention): `tests/test_distribution.py::test_rollback_restores_skills_from_the_selected_build_generator`

## 미실행 항목

- 실제 타 사용자 account의 global install upgrade는 실행하지 않았습니다. 격리 prefix/HOME 시뮬레이션으로 대체했습니다.
- 실제 사용자 project의 migration은 실행하지 않았습니다. v0.1.24 fixture로 검증했습니다.
