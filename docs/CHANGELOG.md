# ForgeFlow 변경 이력

## [0.2.0] - 2026-11-03

### Lean workflow with optional design review

### Changed
- 기본 flow를 단일 agreement/state 기반 lean workflow로 유지하고, 디자인 종료 지점에 선택적 HITL checkpoint를 추가. `workflow start --hitl design`에서만 멈추며 기본은 auto 진행.
- `workflow continue`, `workflow revise`, `workflow stop`으로 설계 검토 결정을 state에 기록.
- `speckit-implement`를 `speckit-tasks`와 짝을 이루는 구현 실행 단계로 명시.
- `tasks/`, `docs/releases/`, strict lifecycle/audit CLI, legacy migration code를 active surface에서 제거. 과거 자료는 `archive/pre-0.2.0` tag에 보존.
- `forgeflow init`은 `tasks/`를 만들지 않고 `.forgeflow/workflows`와 runtime/spec baseline만 구성.
- `forgeflow update`는 현재 0.2.x project만 갱신하며, legacy layout은 `forgeflow-migrate` 안내와 함께 거절.
- 0.1.x user project 정리는 별도 `archive/forgeflow-migrate` branch의 migration tool이 담당.

### Compatibility
- 0.1.x project는 자동 변환되지 않음. `forgeflow-migrate`로 `tasks/`, old strict 자산, legacy docs를 archive tag에 보존한 뒤 제거.
- 완료된 과거 evidence는 archive tag와 Git history에서만 확인.

## [0.1.x] - 2026-10-20 ~ 2026-11-02

Gate 기반 strict lifecycle, Spec Kit 하이브리드 거버넌스, QA-SHA/seal, package 기반 배포를 제공하던 이전 세대. 0.2.0에서 lean/HITL flow로 대체되었으며 active code와 문서에서는 제거되었다.
