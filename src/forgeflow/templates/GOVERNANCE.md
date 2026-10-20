# ForgeFlow Governance

- ForgeFlow bundle version: `0.1.0`

이 문서는 이 프로젝트의 ForgeFlow 운영 규칙 단일 원본입니다. 모든 에이전트는 세션 시작 시 이 문서와 아래의 설치된 규격을 읽어야 합니다.

## ForgeFlow 작업 트리거

사용자가 `forgeflow로 진행`이라고 요청하면 해당 작업은 ForgeFlow lifecycle을 시작하는 요청입니다. 첫 repository write 전에 다음 문서를 읽고 적용합니다.

- [플로우 표준](./spec/FLOW_SPEC.md)
- [Gate와 loop 기준](./spec/GATES_AND_LOOPS.md)
- [변경 이력](./spec/CHANGELOG.md)
- [release 문서 템플릿](./templates/)

`forgeflow` CLI는 문서 준비, release scaffold 생성, 거버넌스 상태 관리 및 Gate audit(`forgeflow check`, 호환 별칭 `harness check`)을 통합 제공합니다. 이는 AI runtime hook이 아니므로, 에이전트는 이 문서의 lifecycle을 직접 준수해야 합니다. v0.6 lifecycle-enabled release는 QA Evidence v2, `RELEASE_SIGNOFF.md`, package manifest와 `.forgeflow/lifecycle/<release-id>.json` Lifecycle State Schema 2를 함께 사용합니다. state는 durable control state이며 historical Evidence v1 release와 default interactive project는 기존 경로를 유지합니다.

## 작업 디렉터리 및 과거 산출물 격리 (Workspace & Historical Isolation)

ForgeFlow는 프로젝트 루트의 `tasks/` (또는 `ff-tasks/`, 레거시 `docs/releases/`)를 순수 작업 패키지 저장소로 사용합니다.

1. **3단 칸반 구조**: `tasks/` 내부는 `backlog/` (기획), `in-progress/` (활성 구현/심사), `completed/` (동결 아카이브)로 구분됩니다.
2. **비-행동지침 경계**: `tasks/` 내부의 파일들은 특정 릴리즈의 작업 산출물 및 증적일 뿐 프로젝트 거버넌스 행동 지침이 아닙니다. 에이전트는 규칙/지침 판단을 위해 `tasks/` (특히 `tasks/completed/`)를 참조하거나 인용해서는 안 되며, 모든 규칙의 단일 진실 공급원(SSOT)은 `docs/spec/`, `docs/forgeflow/GOVERNANCE.md`, 또는 `AGENTS.md`입니다.
3. **레거시 마이그레이션**: 과거 생성된 `docs/releases/` 구조는 `forgeflow migrate --tasks`를 통해 `tasks/completed/`로 일괄 이동하여 현대화합니다.

## Triage와 Gate

모든 repository write 전 요청을 `non-change`, Tier 1, Tier 2, Tier 3으로 분류합니다. non-change는 답변·조사·설명으로 종료합니다. Tier 1은 `CHANGE_NOTE.md`와 self-review를 사용합니다. Tier 2/3은 `forgeflow release create <release-id> --tier <2|3>` (또는 `forgeflow task create`)로 작업 패키지를 만들고, 구현 전에 PRD, DESIGN/RTM 및 Gate 1 검토를 완료합니다. Tier 3은 Security, Reliability, Maintainability 관점의 독립 3인 검토가 필요합니다.

인시던트 해결(`incident-fix`)이나 공용 표면 변경(`public-surface-change`)을 수반하는 릴리즈는 조건부 OIDR(Operational Incident and Delivery Readiness) 트랙이 활성화됩니다. Gate 1에서는 정제된 Incident Brief와 픽스처 매핑을 입증해야 하며, Gate 2에서는 실제 설치된 엔트리포인트에서의 비파괴 프로브를 통해 배포 전달성을 입증해야 합니다.

Gate 1 통과 후에만 격리 workspace에서 구현하고 테스트 실패 시 수정-재테스트 loop를 수행합니다. Gate 2는 `QA Sign-off`입니다. 구현·자동 검증·기술 review를 `QA-SHA`에 결속하고 `PACKAGE_REVIEW_PENDING`에서 멈춥니다. bare `사인오프까지`, `QA Sign-off까지`, `Gate 2까지`는 모두 이 상태를 뜻합니다.

`PACKAGE_FINALIZATION`은 Gate가 아닌 선택적 사용자 release-document 정리 구간입니다. 사용자가 개입하지 않으면 Gate 2 시점 package manifest를 그대로 사용합니다. Gate 3 `Release Sign-off`는 최종 package의 사용자 Go/No-Go이며, 통과 뒤에만 final candidate, Package Seal, strict audit, `COMPLETE`를 진행합니다. `Feature close`는 `COMPLETE`와 별개인 merge/push authority입니다.

## Lifecycle evidence audit

ForgeFlow는 durable lifecycle state와 transition/completion guard를 소유합니다. host adapter는 transport, worker execution, wait, retry, cancellation, result collection을 수행하고 durable Gate/reviewer/artifact/verification evidence는 canonical release artifact에 기록합니다. failed evidence는 strict audit의 unmet condition과 concrete next action으로 보고되며, host transient state는 Gate evidence가 아닙니다.

## Continuation policy 및 로컬 자율 모드

`.forgeflow.json`의 `governance.continuation_policy`는 기본 `interactive`와 opt-in `autonomous`를 구분합니다. 상세 activation, authority boundary, evidence, tiering 규칙은 [Gate와 loop 기준](./spec/GATES_AND_LOOPS.md)을 따릅니다.
- **로컬 단일 에이전트 Attestation 면제**: 로컬 단일 에이전트(LLM-in-the-loop) 환경에서는 암호학적 HMAC 서명 증명(`ActivationAttestation`) 및 nonce CAS가 완전히 면제되며 경량 파일 루프 레코드만으로 자율 모드가 동작합니다.
- **자율 완결 루프 보장**: 사용자의 "계속", "진행", "수정", "해줘" 등 작업 지시는 자율 완결 위임으로 간주하며, 에이전트가 대화형 상태에 머물러 턴을 조기 종료하는 것을 금지하고 Gate 2까지 Loop 2 자가 치유를 완결합니다.

## Gate 2

Tier 2/3은 승격 전에 저장소 루트에서 다음을 실행합니다.

```bash
forgeflow check --all --strict
```

Lifecycle-enabled release는 다음 strict audit도 실행합니다.

```bash
forgeflow check --lifecycle <release-id> --strict --json
```

Evidence v2 strict audit은 Gate 1/2/3 APPROVED, QA-SHA technical review, package manifest, package-only QA-to-final-candidate range, Package Seal, current regular-file artifact를 검사합니다. 하나라도 부족하면 unmet conditions와 정확한 회귀 지점을 확인해 host가 remediation을 수행합니다. 기존 Evidence v1 release는 historical audit을 유지합니다.

Autonomous lifecycle은 파일 시스템 기반의 durable loop record(시도 횟수, no-progress 카운터, failure fingerprint, remediation 목록)를 유지하며, 고신뢰 제어(HMAC attestation, nonce CAS)는 다중 분산 환경에서만 조건부로 요구됩니다. host transient state와 capability cache는 canonical evidence가 아닙니다.

명령, 결과, exit code와 QA 검토 결과를 `docs/releases/<release-id>/QA_SIGNOFF.md`에 기록합니다. commit, merge, push, release, deployment에는 별도 사용자 승인이 필요합니다.

## Completion integrity 및 멈춤 조건 (Stopping Conditions)

### 미완료 Gate 종료 금지 (Completion Integrity)
사용자가 구현·수정·검증을 요청했고 추가 확인이 필요하지 않다면, Gate 2 verdict와 `COMPLETION_REPORT.md`까지 lifecycle을 계속 진행합니다. 단위/통합 테스트 실패, 리뷰어 `REJECT`, 누락 artifact는 최종 응답의 종료 사유가 아니며 즉시 Loop 2 자가 치유를 트리거합니다. 최종 응답은 `Gate 2 APPROVED`와 요구된 검증 PASS가 실제로 확인된 경우에만 완료로 보고합니다.

단, 원인과 무관하게 동일 stage 또는 동일한 n개 stage loop가 5회 연속 다음 stage로 전진하지 못하면(동일 failure fingerprint 누적 5회) 서킷 브레이커를 발동하고 즉시 작업을 중지하여 사용자 지시를 기다립니다.

### 진짜 멈춤 vs 가짜 멈춤 표준 체크리스트

| 구분 | 이벤트 / 상황 | 에이전트의 올바른 자율 행동 (Mandatory) | 금지 행동 (Forbidden) |
| :--- | :--- | :--- | :--- |
| **가짜 멈춤 (Non-Stop)** | 단위/통합 테스트 실패 (`AssertionError` 등) | 즉시 Loop 2 자가 치유(코드/픽스처 수정) 재시도 | 사용자에게 에러 보고 후 턴 종료 |
| **가짜 멈춤 (Non-Stop)** | 코드 리뷰어 `REJECT` 판정 | `REM-xxx` 항목 장부 등록 후 즉시 코드 수정 착수 | 심사 탈락 사실만 전달하고 대기 |
| **가짜 멈춤 (Non-Stop)** | 픽스처 누락, 포맷/타입/린트 오류 | 즉시 픽스처/타입 수정 후 재검증 실행 | 픽스처 불일치를 이유로 중단 |
| **가짜 멈춤 (Non-Stop)** | 서브에이전트 작업 완료 | 결과 취합 후 다음 단계 즉시 디스패치 | 중간 결과 브리핑 후 대기 |
| **진짜 멈춤 (True Stop)** | 동일 failure fingerprint 정확히 5회 연속 무진전 | `BLOCKED` 전이, 5회 실패 이력 보고 후 사용자 지시 대기 | 5회 초과 무한 루프 반복 |
| **진짜 멈춤 (True Stop)** | 사용자 외부 권한 경계 (Git push, 비밀번호/토큰 요구) | 필요 권한/작업 명시 후 승인 대기 | 승인 없는 원격 푸시/파괴적 명령 |
| **진짜 멈춤 (True Stop)** | 아키텍처/명세 모순 발견 (Loop 3 회귀) | RTM/설계 결함 및 회귀 근거 제시 후 승인 대기 | 독단적 기획 임의 수정 |
| **진짜 멈춤 (True Stop)** | Gate 2 승인 후 Gate 3 사용자 릴리즈 대기 | `PACKAGE_REVIEW_PENDING`에서 사용자 Go/No-Go 대기 | 사용자 확인 없는 Gate 3 자동 승인 |

## Feature close command

사용자가 `이 피쳐 클로즈 해줘`라고 명시하면, 이는 이미 committed eligible task
HEAD의 `main` fast-forward merge와 `origin/main` push를 수행할 승인입니다. close는 새 commit을 만들지 않습니다.
먼저 Gate 2 APPROVED, strict lifecycle audit PASS, 필수 artifact 완료, 현재
task branch의 clean candidate를 확인합니다. 하나라도 충족하지 않으면 Git
write 없이 중단하고 unmet condition을 보고합니다.

모든 조건이 충족되면 Gate 2가 심사한 C4 candidate와 그 뒤의 release-evidence-only commit만 포함한 task HEAD를 사용한다. `origin`을 fetch한 뒤 local `main`과 `origin/main` SHA가 정확히 같고
candidate가 그 `main`의 descendant인지 확인한다. 이 조건에서만 task branch를 fast-forward merge하고
`origin/main`에 push합니다. Gate 2 evidence에는 C4 candidate SHA를 고정하고, 성공 후에는 merged/pushed task HEAD SHA와 clean local `main` checkout을
검증합니다. remote divergence, non-fast-forward merge, dirty worktree, 또는
push 실패가 발생하면 rebase, squash, force-push, reset을 하지 않고 중단합니다.

이미 Gate 3 Release Sign-off, Package Seal, `lifecycle complete` 전이가 완료되었거나 `main` 브랜치에 머지된 릴리즈에 대해 클로즈 또는 마무리를 수행할 때는, 전체 회귀 테스트나 하네스 전수 검사 등의 무거운 검증을 재실행하지 않고 `forgeflow lifecycle close <release-id>` 커맨드를 사용하여 0.1초 내에 잔여 격리 브랜치(`feat/<release-id>`) 정리와 워킹 트리 검증을 완결(Fast-Path)합니다.
