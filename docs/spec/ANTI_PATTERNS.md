# 설계 경계

이 색인은 반복 실수를 요약합니다. 상세 규칙은 연결된 소유 문서에 있으며 별도의 Gate를 추가하지 않습니다.

| 피할 패턴 | 적용할 원칙 | 소유 계약 |
| --- | --- | --- |
| 작은 수정마다 다중 서명·seal | 단일 plan/state·project checks·위험별 심사 | [Flow](FLOW_SPEC.md) |
| Readiness/package 완료를 merged로 보고 | ready/integrated/cleaned 구분 | [Flow](FLOW_SPEC.md) |
| Git/worktree 중복 소유·일괄 정리 | owner/source/target/permissions 기록·task-owned 대상만 정리 | [Flow](FLOW_SPEC.md) |
| 무관한 변경의 자동 stage/reset/stash | 사용자 변경 보존·영향 operation만 차단 | [검증](GATES_AND_LOOPS.md) |
| Universal raw Warning 0·기존 finding 전면 수정 | 선언된 checks·Critical/new/existing 구분 | [검증](GATES_AND_LOOPS.md) |
| 기본 QA/candidate/prose seal | 실제 content/동작 검증·Git 실행 ID 허용·strict 명시 호환 | [ADR-005](../adr/005-lean-workflow-and-execution-ownership.md) |
| Current 조용한 변경·날짜 기준 삭제 | 실행 baseline 고정·명시적 adoption·사용자 파일 보존 | [배포](DISTRIBUTION_SPEC.md) |
| 가짜 성공·acceptance 하향 | 실제 동작 수정·영향 검사 재실행 | [검증](GATES_AND_LOOPS.md) |
| installer exit 0·version 문자열만으로 upgrade 성공 | 실제 package/entrypoint/spec/skills 검증 | [배포](DISTRIBUTION_SPEC.md) |
| version/mtime/파일명으로 framework 소유권 추정 | exact content hash·managed manifest로 판정 | [배포](DISTRIBUTION_SPEC.md) |
| 무진전 반복 조사 | 증거·진행 기록·stop rule | [검증](GATES_AND_LOOPS.md) |
| Core의 third-party runtime dependency | Python 3.10+ 표준 라이브러리 | [판단 원칙](PHILOSOPHY_AND_COMPASS.md) |

이전 ADR은 당시 맥락을 보존합니다. ADR-005가 현행 적용 범위를 정의하며 과거 절대적 표현으로 기본 workflow를 덮어쓰지 않습니다.
