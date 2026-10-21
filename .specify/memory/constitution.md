# Project Constitution: Hybrid Governance Rules

## 제1조 (무승인 구현 금지 - No Code Before Gate 1)
어떠한 에이전트도 `tasks/in-progress/<id>/GATE1_REVIEW.md`의 공식 승인(APPROVED) 증적이 존재하지 않는 상태에서 `src/**` 경로에 신규 소스 코드를 생성하거나 기존 코드를 수정할 수 없다. `/speckit.implement`가 호출되더라도 이 원칙이 최우선하며, 위반 시 즉시 실행을 중단하고 사용자에게 보고해야 한다.

## 제2조 (가짜 멈춤 금지 - No False Stopping)
구현 중 발생하는 단순 단위 테스트 실패, 린트 오류, 사소한 컴파일 에러는 사용자에게 턴을 넘기거나 작업을 종료할 수 있는 사유가 아니다. 에이전트는 결함 원인을 스스로 분석하고 코드를 수정하는 내부 자가 치유 루프(Loop 2)를 자율적으로 완주해야 한다.

## 제3조 (원자적 루프 정의 - Atomic Remediation Unit)
자가 치유의 1회 루프는 반드시 `결함 원인 식별 → 코드/테스트 1개 수정 → 테스트 재실행`의 전 과정을 포괄해야 한다. 코드를 수정하지 않고 테스트 명령어만 반복 실행하는 행위는 루프로 인정하지 않으며, 모든 테스트가 통과된 최종 시점에만 원자적 구현 커밋 1개를 생성한다.

## 제4조 (루프 예산 및 진짜 멈춤 - Loop Budget & True Stop)
동일한 에러 핑거프린트로 5회 연속 코드 수정 및 테스트 통과에 실패한 경우에만 작업을 즉시 중지하고 사용자에게 에스컬레이션(진짜 멈춤)한다.

## 제5조 (스펙 무단 하향 금지 - No Spec Downgrade)
구현의 어려움을 이유로 사용자 승인 없이 `spec.md`의 요구사항이나 Acceptance Criteria를 축소·삭제·완화할 수 없다. 스펙 수정이 필요한 경우 반드시 공식 스펙 회귀(Loop 3) 절차를 거쳐 Gate 1 재승인을 획득해야 한다.

## 프레임워크 공식 사양서 참조 경로 (Framework Specifications)
에이전트는 세부 규범과 아키텍처 판단이 필요할 때 다음 공식 사양서(단일 진실 공급원)를 참조해야 한다:
- 참조 인터페이스: `forgeflow doc list` 또는 `forgeflow doc show <spec-name>` CLI
- 전역 템플릿 경로: `~/.local/forgeflow/current/lib/forgeflow/templates/spec/`
- 7대 공식 사양서:
  1. `FLOW_SPEC.md`: 5단계 폐루프 수명주기, 칸반 구조, 브랜치 전략
  2. `GATES_AND_LOOPS.md`: 게이트 판정 기준, 3대 루프(Loop 1~3), 자가 치유 예산
  3. `SPECKIT_HOOKS_AND_NORMS.md`: Spec Kit 3대 주입 메커니즘, 훅 라이프사이클, 체크포인트 커밋 규범
  4. `DISTRIBUTION_SPEC.md`: 배포, 버전 관리, `upgrade` 및 `update` 사양
  5. `PHILOSOPHY_AND_COMPASS.md`: 프레임워크 설계 철학 및 행동 지침
  6. `REFACTORING_GUIDE.md`: 모듈 분리 및 클린 아키텍처 가이드라인
  7. `CHANGELOG.md`: 릴리즈 이력 및 변경 사항
