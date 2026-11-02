# Session checkpoint

갱신: 2026-11-03. Branch: `codex/v0.2.0-hitl-cleanup`.

## 현재 상태

- Base: `main` / `29bc3d3` (v0.1.26)
- Archive: tag `archive/pre-0.2.0`, branch `archive/forgeflow-migrate`
- Working branch: `codex/v0.2.0-hitl-cleanup`
- Version: 0.1.26 (release 시 0.2.0으로 bump)
- Working Tree: 0.2.0 정리 작업 진행 중

## 완료한 범위

- Design-only HITL checkpoint 구현
  - `workflow start --hitl design`
  - `workflow check` → `awaiting-user`
  - `workflow continue/revise/stop`
  - auto flow는 checkpoint 없이 기존과 동일
- strict lifecycle/audit CLI와 전용 module/test 제거
- `tasks/`, `docs/design/issue-12-*`, old ADR/CHANGELOG strict 이력 제거
- `forgeflow init`에서 `tasks/` 생성 제거
- `forgeflow update`를 0.2.x 전용으로 축소, legacy layout은 `forgeflow-migrate` 안내
- 공식 spec/README/AGENTS/skills를 0.2.0 flow로 재작성

## 남은 작업

1. 문서 동기화와 전체 테스트 보정
2. `archive/forgeflow-migrate` branch에 user repo migration tool 작성·검증
3. 0.1.x 기준 증명: HITL, clean init, no legacy CLI, migration tool dry-run/apply, full tests, wheel/install
4. version 0.2.0 bump, tag/release, global install
5. session state 최종 갱신

## 미실행

- PR/merge, 0.2.0 release, global install은 아직 수행하지 않음
