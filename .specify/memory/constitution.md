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

## 제6조 (기획 시 안티패턴 및 ADR 필수 준수 - Anti-Patterns & Architecture Decisions)
에이전트는 과거에 합의된 설계 결정을 망각하고 동일한 실수를 반복해서는 안 된다. 새 기능 기획 및 명세서 작성 착수 시(`speckit.specify` 단계) 반드시 `docs/spec/ANTI_PATTERNS.md`를 필독하여 금지된 안티패턴(Git SHA 결합, 스펙 해시 바인딩 등)을 확인하고, 주요 구조적 변경 시 `docs/adr/`의 아키텍처 결정 레코드를 검토해야 한다.

## 프레임워크 공식 사양서 참조 경로 (Framework Specifications)
에이전트는 세부 규범과 아키텍처 판단이 필요할 때 다음 공식 사양서(단일 진실 공급원)를 참조해야 한다:
- 참조 인터페이스: `forgeflow doc list` 또는 `forgeflow doc show <spec-name>` CLI
- 전역 템플릿 경로: `~/.local/forgeflow/current/lib/forgeflow/templates/spec/`
- 7대 공식 사양서: FLOW_SPEC.md, GATES_AND_LOOPS.md, SPECKIT_HOOKS_AND_NORMS.md, DISTRIBUTION_SPEC.md, PHILOSOPHY_AND_COMPASS.md, REFACTORING_GUIDE.md, CHANGELOG.md
- 안티패턴 및 ADR: docs/spec/ANTI_PATTERNS.md, docs/adr/
