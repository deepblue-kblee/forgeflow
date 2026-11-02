# ADR-001: Lean workflow with an optional design checkpoint

- 상태: Accepted for v0.2.0
- 범위: 현재 workflow. 0.1.x strict lifecycle/audit는 archive tag에 보존하며 현행 선택지가 아니다.

## 결정

ForgeFlow 0.2.x는 하나의 agreement/state로 요구사항부터 검증·통합·정리까지 조정한다. 기본은 자동 진행이며, 사용자가 요청한 경우 디자인 종료 지점에서 한 번 멈춰 spec/plan/tasks와 acceptance를 검토한다.

- 실행 상태는 `.forgeflow/workflows/<id>.json`이 소유한다.
- 설계 checkpoint는 선택적이며 `workflow start --hitl design`으로 활성화한다.
- checkpoint 결정은 `continue`, `revise`, `stop` 세 가지다.
- 구현은 Spec Kit `speckit-implement` 또는 직접 구현을 사용할 수 있다.
- 검증은 프로젝트가 선언한 checks가 소유한다.
- commit/push/merge/cleanup은 agreement에 기록된 권한과 Git/host 소유권을 따른다.
- 0.1.x strict package, QA-SHA, seal, lifecycle audit은 기본 flow가 아니다.

## 결과

기본 auto flow는 중단 없이 끝까지 진행한다. 사용자는 필요한 작업에서만 design checkpoint를 켜서 요구사항과 설계를 직접 확인한다. 과거 strict evidence와 호환 코드는 `archive/pre-0.2.0` tag에 보존하고 active repository에서는 제거한다.
