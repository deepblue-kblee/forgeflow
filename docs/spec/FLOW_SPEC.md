# ForgeFlow 개발 흐름

## 목적과 책임

ForgeFlow는 요구사항부터 계획·구현·검증·허용된 통합·정리까지 완료를 조정합니다. Spec Kit은 계획·태스크 도구, 프로젝트 명령은 검증, Git 또는 owning host는 repository operations를 담당합니다. Core는 Python 3.10+ 표준 라이브러리만 사용합니다.

이 문서는 기본 흐름·agreement·상태 계약을 소유합니다. [GATES_AND_LOOPS.md](GATES_AND_LOOPS.md)는 검증·strict 호환, [DISTRIBUTION_SPEC.md](DISTRIBUTION_SPEC.md)는 setup·runtime 연속성을 소유합니다. docs/spec/가 편집 원본이며 src/forgeflow/spec/는 기계적으로 동기화한 배포 복제본입니다. 완료된 과거 증거는 불변이며 현행 행동 지침을 대체하지 않습니다.

## 기본 흐름

요구사항 → 계획 → 구현 → 검증 → 통합 → 정리 → 완료 보고

두 진행 조건을 유지합니다.

1. 구현 전 scope, 관찰 가능한 acceptance, 작업에 비례하는 plan, 필수 검증 명령을 확정합니다.
2. 통합 전 필요한 검증이 통과하고 해당 operation의 위임 권한이 기록돼 있어야 합니다.

작은 변경에는 짧은 계획을 사용합니다. 복잡한 변경에는 필요한 Spec Kit spec.md·plan.md·tasks.md를 활용합니다. 다중 Gate 서명 문서와 패키지 seal은 기본 요구사항이 아닙니다. 실제 위험이나 프로젝트 정책이 요구하는 추가 심사·외부 승인은 한 번 기록해 적용합니다.

질의·설명·상태 조회는 변경 workflow를 시작하지 않습니다. 대화·프로젝트 정책으로 이미 확보한 승인은 재사용합니다. 새로운 외부 권한, 중대한 범위 확대, 미결 사용자 선택은 확인이 필요할 수 있습니다.

## Agreement와 단일 상태

`forgeflow workflow start <id> --agreement <file.json>`으로 시작합니다. 모든 workflow 명령은 --repo-root와 --json을 지원합니다. 실행 상태의 단일 근거는 .forgeflow/workflows/<id>.json이며 agreement 파일은 최초 입력입니다.

| 필드 | 의미 |
| --- | --- |
| scope | 작업이 소유하는 repository-relative 경로 |
| acceptance | 관찰 가능한 완료 조건 |
| plan | 구현 접근법 또는 Spec Kit 계획 참조 |
| checks | argv 배열 명령; 프로젝트 workflow.checks도 필수로 포함 |
| verification_note | 실행 검사가 필요 없는 변경의 구체적인 검증 근거; 프로젝트 필수 검사를 대체할 수 없음 |
| verification_paths | 검증 입력 경로; 프로젝트 선언 경로는 task에서 제거 불가 |
| owner | standalone 또는 host; branch/worktree operation 소유자 |
| source, target | 정확한 branch; 통합 시 target 필요 |
| integration | none, local, pr; local은 PR 불필요, pr은 owner=host에서만 지원 |
| permissions | 위임한 commit, push, merge, delete-branch, host-cleanup |
| remote | 명시한 remote, 보통 origin |
| task_owned_branch | task가 source branch를 소유하는지 여부 |
| include_existing_changes | 시작 전에 존재하던 scoped 변경을 명시적으로 포함하는지 여부 |

명령은 shell 없이 실행합니다. 실제 프로젝트 검사와 환경 입력을 선언하고 빈 checks나 항상 성공하는 placeholder로 검증을 위장하지 않습니다. permissions가 있어도 프로젝트 보호 규칙은 유지됩니다.

## 명령과 관찰된 진행

~~~text
forgeflow workflow start <id> --agreement agreement.json
forgeflow workflow check <id>
forgeflow workflow verify <id>
forgeflow workflow status <id>
forgeflow workflow finalize <id>
forgeflow workflow finalize <id> --receipt host-receipt.json
forgeflow workflow adopt <id> --reason "변경 이유" --impact "영향 검토"
~~~

check는 구현 준비를 검증합니다. verify는 project/task checks를 실행하고 관련 content에 결과를 기록합니다. status는 관찰된 진행·blocker·다음 행동을 제공합니다. finalize는 허용된 operation을 수행하거나 pending host action을 반환합니다. adopt는 영향 검토 후 baseline을 명시적으로 변경합니다.

| 상태 | 확인된 사실 |
| --- | --- |
| ready | 관련 content의 필수 검증 통과 |
| integrated | 선택한 target에 승인된 source 변경이 포함됨 |
| cleaned | 소유 도구를 통한 허용된 task-owned 정리 완료 |

요청한 위임 범위의 완료는 finalization_complete로 기록합니다. readiness-only 작업은 ready를 유지하면서 완료할 수 있으며 이를 merge라고 보고하지 않습니다. 정리를 요청하지 않은 통합도 integrated에서 위임 완료될 수 있습니다. pending action이 있으면 완료 flag를 세우지 않습니다.

## Git과 host 소유권

기존 host-managed checkout은 host 소유권을 유지합니다. legacy auto_create_branch가 true여도 workflow 시작·검증으로 중복 branch/worktree를 만들지 않습니다. Core는 vendor 전용 API 대신 pending action과 실행 receipt 경계로 host 작업을 연결합니다.

Project workflow.owner=host는 durable ownership 경계입니다. Task agreement에서 standalone으로 덮어써 Git operation을 직접 실행할 수 없습니다. 소유권 변경은 owning host와 사용자 범위에 맞는 명시적 migration으로 별도 판단하며 이미 시작한 task의 권한을 조용히 넓히지 않습니다.

PR operation은 owner=host로 위임하며 standalone+pr 조합은 시작 시 거절합니다. Receipt에는 repository 절대 경로·source·operation·tool·구체적 evidence를 기록합니다. Merge에는 target·검증된 source_commit이 필요하고 core가 target ancestry와 tree 일치를 관찰합니다. Delete-branch는 task 소유권·통합 완료·실제 branch 부재로 확인합니다. Core가 독립 확인할 수 없는 host checkout archive 등은 owning tool의 외부 완료 경계로 남기며 가짜 cleaned 영수증으로 처리하지 않습니다.

Standalone finalize는 commit 권한이 있을 때 합의된 scope만 stage/commit합니다. 해당 권한이 없으면 source에 작업 commit이 이미 있어야 합니다. Push·merge·branch 삭제는 각각 권한이 필요하며 readiness만으로 이를 추정하지 않습니다.

통합 직전에 repository·source/target·ownership·검증 freshness를 확인합니다. Local merge는 --ff-only를 사용하며 divergence는 조정과 영향받는 재검증을 요구합니다. 코드·환경·target 이동·충돌 해결로 검증 결과가 달라질 수 있으면 해당 결과를 확인합니다. Report/receipt 변경만으로 전체 테스트를 반복하지 않습니다.

Push/통합 결과는 선언된 검증 입력을 포함한 accepted source commit tree와 일치해야 합니다. Scope 밖 dirty dependency로 검증한 결과를 그 변경이 빠진 commit의 성공으로 취급하지 않습니다. 정확한 committed-input guard와 보수적 기본 입력 범위는 [검증 계약](GATES_AND_LOOPS.md)을 따릅니다.

관련 없는 dirty 파일은 보존합니다. 이를 몰래 stage/stash/reset/삭제하지 않습니다. 정리는 권한을 확보한 task-owned 대상에 한정합니다. Host checkout archive는 owning tool로 수행하고 외부 receipt로 연결하며 core가 성공을 꾸미지 않습니다.

## 재개와 마이그레이션

통합 성공을 정리보다 먼저 기록합니다. 정리가 실패하면 integrated를 보존하고 정리만 재시도합니다. 다시 merge하거나 영향 없는 검증을 열지 않습니다. 외부 operation 기록을 불변 strict 패키지 안에 덧쓰지 않습니다.

새 작업은 기본 workflow를 사용합니다. 기존 strict lifecycle·evidence는 명시적 호환 경로로 유지합니다. 진행 중 작업은 명시적 adoption 전까지 baseline을 유지하고 완료 archive는 보존합니다. 파일명 변경이나 가짜 승인으로 마이그레이션을 위장하지 않습니다.

Legacy project 이전은 `forgeflow update --dry-run --json`의 inventory/plan으로 시작합니다. Active work, unresolved user conflict, plan drift는 write 전에 차단하며 blocker는 task/baseline/pinned command 또는 specific conflict path와 next action을 포함합니다. `update --accept <path>`는 plan이 보고한 특정 conflict만 해소하고, `update --recover <id>`는 실패한 migration record에서 managed path만 복구합니다. 적용되지 않은 conflict를 success로 보고하지 않습니다.
