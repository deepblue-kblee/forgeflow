# 검증·심사·복구 규칙

기본 workflow는 [FLOW_SPEC.md](FLOW_SPEC.md)가 정의합니다. 이 문서는 검증 정책과 유지하는 strict lifecycle 호환 경계를 소유합니다.

## 필수 검증

프로젝트가 선언한 test/lint/build를 우선 사용합니다. Project workflow.checks는 필수이며 task checks는 이를 추가합니다. 실제 명령·환경·exit result·관련 content를 기록합니다. Task에서 project checks를 없애거나 결과를 위조하거나 서명을 실행 성공으로 대체할 수 없습니다.

변경 동작·실제 연결·사용자가 받는 entrypoint를 확인합니다. 작업 중 focused 검사를 사용하고 통합 전 필요한 관련 suite를 실행합니다. 코드·환경·통합 결과·검증 입력이 바뀌면 해당 검사를 재실행합니다. 동일 증거를 단계마다 만들거나 report/checkbox 변경만으로 전체 테스트를 반복하지 않습니다.

verification_paths는 project/task 선언을 합치며 task 미지정 시 scope를 더합니다. 명시된 입력이 전혀 없으면 tracked dependencies를 보수적으로 확인합니다. 명시적 입력에서 tasks.md·session-state 등 완료 메타데이터를 제외하면 그 문서만 바뀐 경우 검증을 재사용할 수 있습니다. 정확한 입력을 선언하지 않은 채 의존 코드 변경을 메타데이터 변경으로 취급하지 않습니다.

기본 환경 입력 PATH/PYTHONPATH/PYTHONHOME/VIRTUAL_ENV/CONDA_PREFIX/NODE_PATH/NODE_OPTIONS와 선언 환경의 digest를 확인합니다. 검증 기록에 민감한 환경 원문을 노출하지 않습니다.

forgeflow review는 프로젝트가 필수로 선택한 경우 외에는 선택적 AST 보조 도구입니다. 수치 임계치를 모든 작업의 blocker로 삼지 않습니다.

- Raw strict: forgeflow review --strict는 선택 scope의 Warning 0건을 요구합니다.
- Baseline strict: forgeflow review --strict --findings-baseline <ref>는 Critical·신규 Warning 0건을 요구합니다. 기존 findings는 표시하며 Counter slot matching으로 중복 발생량을 구분합니다.

선택한 정책으로 project 필수 검사를 무시하거나 실제 회귀를 숨길 수 없습니다. 관련 없는 기존 findings 때문에 작은 작업을 전면 refactor로 확대하지 않습니다.

## 위험에 비례하는 심사

작은 가역 변경에는 짧은 계획과 유효한 검증을 사용합니다. 실제 위험·프로젝트 정책이 요구할 때 설계 심사, 독립 security/reliability review, 설치 probe, 외부 승인을 추가합니다. 요구사항을 한 번 기록하고 유효한 증거를 재사용합니다.

ForgeFlow의 이번 default 전환은 governance·operation authority를 바꾸므로 독립 Security/Reliability/Maintainability 설계·최종 심사를 유지합니다. 이 전환 요건을 모든 downstream 변경의 상시 3인 panel 의무로 확대하지 않습니다.

## Content·dirty 작업·provenance

검증 freshness는 관련 content와 명령·환경을 따릅니다. Git ref·commit ID는 push/merge 같은 실행 사실을 기록할 수 있습니다. 기본 workflow는 QA-SHA/Candidate-SHA seal이나 prose-spec hash를 요구하지 않습니다.

관련 없는 dirty 파일은 그대로 둡니다. 관련 미commit 변경이 특정 operation을 막으면 소유권을 해소합니다. 모든 작업에 global clean status를 강제하거나 사용자의 변경을 몰래 commit/stash/reset하지 않습니다.

Push/통합 전에는 선언된 verification input의 working content가 accepted source commit tree에 포함되는지 확인합니다. Scope 밖의 미commit dependency를 사용해 PASS했지만 source commit에 그 내용이 없으면 verify-committed-inputs로 해당 operation을 차단하고 파일을 보존합니다. 기본 all-tracked 검사는 보수적으로 이 차이를 포함합니다. 실제로 무관한 파일은 verification_paths로 검증 입력을 정확히 선언해 제외할 수 있지만, 필요한 dependency를 검증에서 빼거나 몰래 commit해 통과시키지 않습니다. 필요하면 owning tool이 준비한 committed 결과를 독립 검증합니다.

## 진행·중단 규칙

실패 원인을 파악하고 관련 수정을 한 뒤 영향받는 검사를 실행합니다. 조사도 비용을 소모합니다. 같은 자료 조회·무변경 명령 반복은 전진이 아닙니다. Failure·시도한 해결·새 증거·다음 행동을 기록합니다.

반복 실패에는 설정된 no-progress budget(통상 5회)을 적용합니다. 외부 권한·필수 외부 승인·필수 capability·중대한 사용자 결정이 없으면 그 단계에서 먼저 막힐 수 있습니다. 차단 단계와 다음 행동을 보고하고 실제 재실행 성공 전에는 실패를 통과로 바꾸지 않습니다.

## 명시적 strict 호환 경로

기존 release/task/lifecycle/archive-audit 명령은 과거 또는 의도적으로 선택한 strict 패키지를 지원합니다. 기본 workflow 명령을 정의하지 않습니다. 완료 패키지의 과거 정책·증거는 소급 변경하지 않습니다.

Strict 패키지는 명시적으로 선택한 git-sha 또는 sha-free를 유지합니다. [ADR-005](../adr/005-lean-workflow-and-execution-ownership.md)는 과거 SHA 전면 금지의 적용 범위를 한정합니다. Historical strict binding과 일반 Git 실행 ID는 지원하며 lean 기본 흐름에는 QA/candidate seal이 없습니다.

Strict 실행 순서:

1. Spec/plan/tasks와 위험별 심사를 정리하고 구현 전 GATE1_REVIEW.md를 승인합니다. forgeflow check <id> --stage 2로 strict entry evidence를 확인합니다.
2. 구현·필수 검증 후 실제 reviewer/result와 선택 policy를 갖춘 QA_SIGNOFF.md 및 Evidence v2를 준비합니다.
3. forgeflow lifecycle package-review <id> <qa-sha> 또는 forgeflow lifecycle package-review <id> --sha-free로 package review에 진입합니다.
4. 문서·manifest와 승인된 RELEASE_SIGNOFF.md를 준비하고 해당 패키지가 요구하는 인간 승인을 확인합니다.
5. forgeflow lifecycle seal <id> <candidate-sha> 또는 forgeflow lifecycle seal <id> --sha-free 후 forgeflow lifecycle complete <id>를 실행합니다.

Strict seal의 clean worktree·package manifest 조건은 사전에 선언합니다. 조건을 맞추려고 두 번째 worktree를 몰래 만들거나 무관한 사용자 작업을 바꾸지 않습니다. Package review와 RELEASE_SIGNOFF.md는 seal보다 먼저이며 strict 완료는 merge/push/delete 권한을 부여하지 않습니다.

진행 중 승인 패키지의 정책을 명확히 할 때 유효한 구현·검증 증거는 유지하고 영향받는 evidence만 명시적 검토 후 갱신합니다. Runtime adoption과 strict-package policy migration은 별개이며 완료 증거는 불변입니다.
