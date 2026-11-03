# Session checkpoint

갱신: 2026-11-03. Base: `main`.

## 현재 상태

- PR #15 merge commit: `3bff95f`
- Patch: PR #16 merge commit `3104474`
- Version: 0.2.1 (`src/forgeflow/_version.py`, `docs/spec/VERSION`)
- Working Tree: clean
- Archive: tag `archive/pre-0.2.0`, branch `archive/forgeflow-migrate`

## 배포판 현황

- Local Artifacts: `dist/forgeflow-0.2.1-py3-none-any.whl`, `dist/forgeflow-0.2.1.tar.gz`
- Git Tag: `v0.2.0`, `v0.2.1` push 완료
- GitHub Releases: `v0.2.0`, `v0.2.1` 등록 완료
- Active User Distribution: v0.2.1 설치 완료 (`~/.local/share/forgeflow/current`, `~/.local/bin/forgeflow`)
- Entrypoint `workflow --help`, version, skills probe 통과

## 완료한 범위

- Design-only HITL checkpoint: `workflow start --hitl design` → `check` → `continue/revise/stop`
- 기본 auto flow는 checkpoint 없이 기존과 동일
- 0.1.x strict lifecycle/audit CLI, legacy modules, tasks/docs artifacts, old tests/fixtures 제거
- `forgeflow init`의 `tasks/` 생성 제거
- `forgeflow update`는 0.2.x 전용, legacy layout은 `forgeflow-migrate` 안내
- 공식 spec, README, AGENTS, generated skills를 0.2.x 전용으로 재작성
- Archive branch `archive/forgeflow-migrate`에 user-project migration tool 작성 및 v0.1.24 fixture로 dry-run/apply 검증

## 검증

- `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"` → 216 tests OK
- `python3 scripts/sync-distribution.py --check` → match
- 0.2.0/0.2.1 wheel/tar.gz build 및 격리 venv install
- HITL checkpoint → continue → verify → finalize 실제 Git repo 검증
- package에 lifecycle/harness/migration legacy module 미포함 확인

## 남은 작업

1. 실제 사용자 project는 `archive/forgeflow-migrate` branch의 `forgeflow-migrate.py`로 정리 후 0.2.0 적용
2. Issue #14의 M05/M06/M07/U06 보강은 별도 후속 검증 범위

## 미실행

- 실제 사용자 project migration은 실행하지 않음
