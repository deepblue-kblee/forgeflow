# ForgeFlow 공식 명세 색인

ForgeFlow 0.2.x는 단일 agreement/state로 설계·구현·검증·통합·정리를 조정합니다. 디자인 종료 지점의 사용자 checkpoint는 선택적입니다.

| 질문 | 소유 문서 |
| --- | --- |
| 흐름·agreement·HITL checkpoint·CLI·완료 | [FLOW_SPEC.md](FLOW_SPEC.md) |
| 검증·실패 처리·review | [GATES_AND_LOOPS.md](GATES_AND_LOOPS.md) |
| Setup/update·배포·runtime baseline | [DISTRIBUTION_SPEC.md](DISTRIBUTION_SPEC.md) |
| Spec Kit 위임과 선택적 도구 | [SPECKIT_HOOKS_AND_NORMS.md](SPECKIT_HOOKS_AND_NORMS.md) |
| 설계 경계 | [ANTI_PATTERNS.md](ANTI_PATTERNS.md) |
| Refactoring·선택적 AST review | [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) |
| 목적·판단 원칙 | [PHILOSOPHY_AND_COMPASS.md](PHILOSOPHY_AND_COMPASS.md) |

`docs/spec/`가 편집 원본이며 `src/forgeflow/spec/`는 기계적 배포 복제본입니다. Active task는 실제 runtime/spec content identity와 실행 가능한 snapshot을 유지합니다. 과거 0.1.x strict lifecycle/audit은 현행 flow가 아니며 `archive/pre-0.2.0` tag에 보존합니다.
