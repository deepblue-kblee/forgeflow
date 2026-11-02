# Issue #12 verification record

## 실행 환경

- macOS (Apple Silicon), Python 3.14.5
- 실행 entrypoint: source tree `PYTHONPATH=src python3 -m forgeflow.cli`
- 격리 fixture: temp HOME/prefix/bin/skills, local `file://` source와 local Git repository
- 실제 사용자의 global install, project, remote branch는 변경하지 않음

## 필수 검사

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"
# Ran 444 tests in 65.839s — OK

python3 scripts/sync-distribution.py --check
# Distribution documents match canonical sources.
```

## Issue matrix 대응

| ID | 검증 | 결과 |
| --- | --- | --- |
| M01 | `tests/test_migration.py::test_m01_unmodified_v0124_project_becomes_lean` — 실제 v0.1.24 생성물 fixture, lean 전환, baseline 생성, `python3 .forgeflow/run.py version`, 2회 no-op | PASS |
| M02 | 사용자 수정 constitution 보존, exit 3, `--accept` 후 backup과 lean bytes 확인 | PASS |
| M03 | legacy config-only, custom tasks_dir, legacy config 보존 | PASS |
| M04 | active workflow 차단, task/baseline/pinned command 보고, write 0건 | PASS |
| M08 | dry-run filesystem 불변, plan 이후 수정 시 `plan-drift`, CLI dry-run exit 0 | PASS |
| M09 | 두 번째 write 실패 주입 후 managed bytes 복원, journal/backup 경로 보고 | PASS |
| M10 | applied report의 created/updated/preserved/backup/journal을 실제 filesystem과 대조 | PASS |
| U01 | `tests/test_upgrade_integration.py` — 실제 installer subprocess, metadata/entrypoint/spec/skills 검증, custom prefix 무env 해소 | PASS |
| U02 | no-op installer, wrong version, missing installation, installer failure가 비성공 | PASS |
| U04 | same-version different build detector | PASS (unit) |
| U05 | skills target 실패 시 이전 current/bin entrypoint 유지 | PASS |

## 확인한 한계

- GitHub remote main 이동, branch protection, 실제 Codex host 동작은 실행하지 않았습니다.
- Python 3.10 runtime에서 전체 suite를 실행하지 않았습니다. `from __future__ import annotations` 적용과 `typing.get_type_hints` 회귀 재현으로 annotation NameError를 수정했습니다.
- M05/M06/M07의 모든 host/symlink 변형과 U06 retention 실패 주입은 대표 case만 자동화했습니다. 관련 code path는 `preflight_baseline`, `_recovery_target`, distribution tests로 보장하지만 전체 matrix 실행 완료로 보고하지 않습니다.
- installer가 SIGKILL로 중단되면 shell trap이 실행되지 않습니다. 다음 실행은 staging/완전성 검사로 복구하지만 단일 atomic transaction은 아닙니다.
