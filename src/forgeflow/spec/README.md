# ForgeFlow 공식 명세 색인

기본 workflow는 하나의 task state와 프로젝트 검증으로 사용자가 허용한 완료 지점까지 조정합니다. 기존 strict lifecycle evidence는 명시적 호환 경로입니다.

| 질문 | 소유 문서 |
| --- | --- |
| 흐름·agreement·CLI·Git/host ownership·완료/복구 | [FLOW_SPEC.md](FLOW_SPEC.md) |
| 필수 검증·위험별 심사·복구·strict 호환 | [GATES_AND_LOOPS.md](GATES_AND_LOOPS.md) |
| Setup/update·배포·content identity·pinned runtime | [DISTRIBUTION_SPEC.md](DISTRIBUTION_SPEC.md) |
| Spec Kit 위임·선택적 hook | [SPECKIT_HOOKS_AND_NORMS.md](SPECKIT_HOOKS_AND_NORMS.md) |
| 설계 경계 | [ANTI_PATTERNS.md](ANTI_PATTERNS.md) |
| Refactoring·선택적 AST review | [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) |
| 목적·판단 원칙 | [PHILOSOPHY_AND_COMPASS.md](PHILOSOPHY_AND_COMPASS.md) |

docs/spec/가 편집 원본이며 src/forgeflow/spec/는 생성 복제본입니다. 양쪽을 수동 유지하지 않습니다. Task는 실제 runtime/spec content identity를 기록합니다. VERSION만으로 same-version replacement를 감지할 수 없습니다. 명시적 adoption까지 pinned baseline을 사용합니다. 여러 active task의 기준이 다르면 state의 baseline.command를 통한 doc show 또는 baseline.path/spec를 우선합니다. .forgeflow/spec 링크는 프로젝트 기본/새 작업 편의 진입점입니다. 과거 archive/changelog는 이전 동작의 기록이며 현행 지침이 아닙니다.
