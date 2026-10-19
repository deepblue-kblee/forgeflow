# 🚦 ForgeFlow 게이트 기준 및 순환 루프 규칙 (GATES_AND_LOOPS.md)

- **버전**: v0.20.0 (Operational Incident and Delivery Readiness Track)
- **상태**: Approved
- **최종 수정일**: 2026-10-17

---

## 1. 위험도 등급 체계 (Risk Tiering Matrix)

과업의 복잡도와 위험도에 따라 게이트 검증 강도를 3단계로 분기하여 오버헤드를 최적화하고 보안 무결성을 보장한다.

### 작업 분류와 최우선 판정 규칙 (Mandatory Triage)
- 모든 요청은 첫 repository write 전에 `non-change`, Tier 1, Tier 2, Tier 3으로 분류한다. 질문 응답, 조사, 설명, status 확인처럼 filesystem, repository, configuration, infrastructure, release artifact를 수정하지 않는 요청은 `non-change`이며 release lifecycle 대상이 아니다.
- **도메인 위험도와 불확실성은 코드 라인 수보다 항상 우선한다.** 하나의 Tier 3 signal이라도 일치하거나 diff 분석·분류가 불가능하면 Tier 3으로 fail-closed 처리한다.
- Tier 3 signal: auth, authorization, token, secret, encryption, payment, personal data, permission, dependency/supply-chain, destructive data operation, persistence/schema migration, network boundary, external API, core daemon, concurrency, CI/CD, deployment, configuration, public API/CLI, 3개 이상 module I/O contract, 또는 `AGENTS.md`, `docs/spec/**`, governance template, tiering/reviewer/gate/validator policy 변경.
- Tier 1은 동작 불변 문구·formatting·일반 documentation 또는 다음을 모두 충족하는 단일 module의 재현 가능한 국소 bugfix에 한정한다: security·permission·data boundary 영향 없음, public interface·data·configuration 변경 없음, 기존 재현 test PASS 가능, rollback 명확. test 추가·수정은 Tier 2 이상이다.
- Tier 2 signal: Tier 3 또는 Tier 1에 해당하지 않는 실행 코드, test, build, rollback이 불명확한 변경, 또는 요구사항 해석이 필요한 bugfix.

| 등급 | 필수 artifact와 Gate 1 | Gate 2 및 승격 |
| :--- | :--- | :--- |
| **Tier 1 (Minor)** | 변경 전 `docs/releases/<release-id>/CHANGE_NOTE.md`에 scope, planned changed paths, Tier 1 rationale, risk signals 없음, rollback, Gate 1 self-review `PASS`를 기록 | actual changed paths와 planned scope를 self-review로 대조하고 관련 lint/unit test 또는 문서 검증을 PASS한다. 명령·결과·exit code·Gate 2 self-verdict `PASS`를 같은 파일에 기록하며, verdict는 checklist 전체 완료와 planned scope 일치를 인증한다 |
| **Tier 2 (Standard)** | PRD, DESIGN/RTM 및 독립 senior reviewer 1인 자문 | Gate 2 QA Sign-off 뒤 package review, Gate 3 Release Sign-off |
| **Tier 3 (Critical)** | PRD, DESIGN/RTM 및 Security·Reliability·Maintainability 관점의 독립 3인 병렬 panel | QA-SHA의 독립 3인 technical review, Gate 2 QA Sign-off, Gate 3 package Go/No-Go |

---

## 2. 게이트 정의 및 통과 기준 (Gate Criteria)

### Gate 1: 사전 기획/설계 승인 게이트 (Pre-Implementation Gate)
- **위치**: Stage 2 종료 시점 (Stage 3 격리 구현 진입 직전)
- **통과 요건**:
  1. Tier 1은 변경 전 `CHANGE_NOTE.md`와 self-review PASS를 확정한다. Tier 2/3은 PRD에 `REQ-ID` 기반 요구사항·인수 조건, DESIGN에 아키텍처·RTM을 작성한다.
  2. 등급별 심사 통과:
     - Tier 1: planned changed paths가 허용 범위와 일치하는지 self-review로 확인한다. actual changed paths 대조는 Gate 2에서 수행한다. checklist 누락·검증 실패·unplanned path·risk signal·불확실성은 PASS를 금지하고 상위 Tier로 재분류한다.
     - Tier 2: 독립 시니어 심사관 1인 자문 의견 검토 및 설계 보완 완료.
     - Tier 3: **Security, Reliability, Maintainability 3대 관점의 독립 심사관(Parallel Panel)**에게 병렬 1회 자문(Fan-Out) ➔ 독립 피드백 취합(Fan-In) 후 사령관이 핵심 결함을 보완하여 최종 확정.
   3. **보안/치명 결함 거부권 (Blocker Veto)**: Tier 3 panel 중 1인이라도 security 또는 destructive Blocker를 제기하면 수정 후 해당 reviewer의 재확인 또는 명시적 사용자 risk acceptance 없이는 통과할 수 없다.
   4. **조건부 OIDR 인시던트 적합성 심사 (Incident Applicability Review)**: 인시던트 해결(`incident-fix`), 공용 표면 변경(`public-surface-change`) 또는 운영 클레임(`operational-claim`)을 수반하는 릴리즈는 결정론적 트리거 강제 도출에 의해 OIDR 트랙이 강제 활성화되며(`none` 우회 불가), PRD 내 정제된 `Incident Brief`와 4단 정형 매핑(`PROP-<ID> -> FIXTURE-<ID> -> ORACLE-<ID> -> REQ-<ID>`)을 검증한다. `Applicability Verdict`는 `supported`, `explicitly-excluded`, `discovery-only` 중 하나여야 하며, `supported` 평결은 모든 핵심 결함 특성에 대해 중복/플레이스홀더 없는 1:1 바인딩이 증명되어야 승인된다.

### Gate 2: QA Sign-off Gate
- **위치**: Stage 4 구현/테스트 완료 뒤, release package 사용자 검토 전
- **통과 요건**:
  1. Tier 1은 `CHANGE_NOTE.md`의 scope·planned changed paths와 Gate 2 증적이 충족되어야 한다. Tier 2/3은 PRD의 모든 `REQ-ID` 요구사항을 충족해야 한다.
  2. ForgeFlow self-maintenance release는 canonical version, base-to-target bump,
     structured version evidence, release-ID prefix, and dynamic package metadata
     verification을 충족해야 한다. 하나라도 누락되거나 불일치하면 Gate 2는 PASS할 수 없다.
  3. Tier 1은 해당 변경에 적합한 verification command 또는 명시적 대체 검증을 성공해야 한다. Tier 2/3은 모든 단위/통합 테스트를 통과해야 한다 (Failure = 0, Error = 0).
  4. Tier 2/3은 런타임 및 정적 분석(Linter/Type Check) 오류가 0건이어야 한다.
  5. 등급별 서명 발급:
     - Tier 1: `CHANGE_NOTE.md`에 actual changed paths, 검증 명령·결과·exit code와 PASS self-verdict를 기록한다. verdict는 checklist 전체 완료와 planned scope 일치를 명시적으로 인증한다. checklist 누락·검증 실패·unplanned path·risk signal·불확실성·skip·conditional·negated verdict는 PASS와 promotion을 차단하고 상위 Tier로 재분류한다.
     - Tier 2: 독립 QA 심사관의 단독 심사 후 `QA_SIGNOFF.md` 발급.
     - Tier 3: **Security, Reliability, Maintainability 3대 관점 독립 패널 검증관**의 병렬 코드/테스트 심사 의견을 사령관이 취합하고 결함 해소 확인 후 `QA_SIGNOFF.md` 발급.
  6. QA-SHA는 full test가 통과한 C4 snapshot이다. `QA_SIGNOFF.md`의 Evidence v2와 Tier reviewer는 이 SHA만 승인한다.
  7. 통과하면 lifecycle은 `PACKAGE_REVIEW_PENDING`으로 전이한다. `QA Sign-off까지`, `Gate 2까지`, 또는 bare `사인오프까지`는 이 상태에서 멈추라는 사용자 지시다.
  8. **조건부 Consumer Delivery Readiness (소비자 전달성 검증)**: 공용 CLI/API 표면 변경이 수반된 릴리즈는 소스 체크아웃이 아닌 격리 설치 환경에서 비파괴 프로브(Non-mutating probe)를 실행하여 런타임 전달성을 증명해야 하며, 후보 아티팩트 Identity/Digest 결속, 소스 체크아웃 누출 차단, 활성 타깃 미검증 시 명시적 waiver(`delivery ready; active target unverified`)를 기록해야 한다.

### PACKAGE_FINALIZATION: 선택적 사용자 문서 정리

- Gate가 아니다. 사용자는 Release Notes, Completion Report와 release 문서를 정리하거나 추가할 수 있다.
- 사용자가 개입하지 않으면 no-op이며 Gate 2 시점 package manifest가 그대로 다음 Gate의 검토 대상이다.
- package 이외의 구현·테스트·spec/config 변경은 허용하지 않으며 Gate 2를 무효화하고 구현/검증 loop로 회귀한다. 단, 수명주기 제어 평면 상태(`.forgeflow/lifecycle/{release_id}.json`)의 정상 전이 및 세션 상태 기록(`docs/session-state/`)은 패키지 결속 허용 경로로 인정한다.

### Gate 3: Release Sign-off Gate

- **위치**: `PACKAGE_FINALIZATION` 뒤, final candidate 생성 전
- **목적**: 사용자 또는 release authority가 최종 release package manifest를 Go/No-Go로 판정한다. Security/Reliability/Maintainability 기술 review를 반복하는 Gate가 아니다.
- **통과 요건**: `RELEASE_SIGNOFF.md`의 Gate 3 `APPROVED`/`GO`, manifest digest, package regular-file/digest와 allowed path가 일치해야 한다.
- **통과 후**: automation이 `Release-Candidate-SHA`를 생성하고 Package Seal 및 strict audit을 수행한다. 그 결과만 `COMPLETE`가 될 수 있다.
- **실패/수정**: release 문서·manifest 문제는 `PACKAGE_FINALIZATION`으로만 회귀한다. QA-SHA 이후 implementation path가 바뀐 경우에는 Gate 2부터 다시 수행한다.

### 💡 고밀도 경량 검증 컨텍스트 프로토콜 (Lightweight Context Protocol)
Tier 3 패널 심사 시 토큰 낭비를 방지하기 위해 심사관 에이전트에게 프로젝트 전체 코드를 전달하지 않고 아래 3대 핵심 아티팩트만 주입한다.
1. **Git Diff**: 격리 워크스페이스 변경분 요약 (`git diff`)
2. **테스트 실행 로그**: `pytest` / 회귀 테스트 결과 리포트 요약
3. **요구사항 매핑표(RTM)**: `PRD.md` 및 `DESIGN.md`의 `REQ-ID` 충족 여부 체크리스트

### 🎯 패널 관점 분리 지침 (Perspective Diversity)
3인 패널 호출 시 모델의 동조화 맹점(Mode Collapse)을 방지하기 위해 각 인스턴스에 고유한 평가 포커스를 주입한다.
- **패널 1 (Security & Auth)**: 권한 탈취, 2FA 우회, 시크릿 유출, 인젝션 취약점 검증.
- **패널 2 (Reliability & Edge Cases)**: 비동기 레이스 컨디션, 타임아웃, 예외 처리, 경계값 오류 검증.
- **패널 3 (Maintainability & QA)**: RTM 요구사항 누락, 코드 가독성, 부작용(Side-effect) 및 테스트 커버리지 검증.

---

### 재분류 및 증적 연속성 (Escalation Record)
작업 중 checklist 누락, verification 실패, unplanned path, risk signal, scope 확대, reviewer 지적, declared path와 actual diff 불일치, 또는 분석 불가가 발생하면 즉시 write와 promotion을 중지하고 상위 Tier로 재분류한다. 하향 분류는 허용하지 않는다.

- 재분류 기록에는 base commit, 최초 tier와 판정 시각, escalation trigger, 기존 `CHANGE_NOTE.md` 또는 review evidence의 참조와 snapshot을 남긴다.
- Tier 1에서 Tier 2/3으로 상향할 경우 기존 triage와 diff를 보존하고, 격리 workspace에서 PRD, DESIGN/RTM, 해당 Tier의 Gate 1을 완료한 뒤에만 구현을 재개한다.
- `CHANGE_NOTE.md`는 정해진 Markdown section으로 scope, planned changed paths, Tier 1 rationale, risk signals 없음, rollback, Gate 1 self-review, actual changed paths, verification command/result/exit code, Gate 2 self-verdict를 기록한다.
- 후속 validator는 이 경량 sign-off를 검사할 수 있으나, Tier 1의 선행 조건은 아니다. 외부 side effect에는 항상 별도 사용자 승인이 필요하다.

---

## 3. 자가 치유 순환 루프 규칙 및 서킷 브레이커 (Loop & Circuit Breaker)

### Loop 1: 사전 설계 피드백 반영 루프 (Design Refinement Loop)
- **트리거**: 독립 심사관 피드백에서 아키텍처 결함, 보안 취약점, 계약 불완전성, 인터페이스 모호성 또는 복구/데이터 보존 결함 지적 시.
- **처리 원칙**: 사령관이 피드백을 수렴하여 설계를 보완하고 필요 시 재자문 수행 (최대 5회 반복 제한).
- **서킷 브레이커**: 5회 반복에 도달해도 자동 승인(Auto-Approval)을 엄격히 금지한다. 미해결 지적사항(unresolved findings)이나 심사관 REVISE/BLOCK이 잔존할 경우 Gate 1을 `PENDING`으로 유지하고, 사용자 및 승인 권한자(Authority)에게 재기획, 범위 축소 또는 위험 수용(Risk Acceptance) 결정을 요청한다.
- **기록 의무**: 매 라운드는 동결된 baseline commit SHA, 변경 경로, 지적사항 조치 내역(disposition), 심사관 관점별 평가 및 판정을 Gate 1 evidence에 명시적으로 기록한다.

### Loop 2: 코드 레벨 자가 수정 루프 (Code-Level Fix Loop)
- **트리거**: Stage 4에서 단위/통합 테스트 실패, 런타임 예외, 구문 오류 발생 시.
- **테스트 무결성 규칙**: 테스트 코드를 임의로 삭제하거나 어설션을 약화하는 행위 금지 (구현 코드 우선 수정).
- **서킷 브레이커**: 최대 5회 수정 반복 제한. 5회 연속 실패 시 Loop 3(아키텍처 회귀) 강제 전이.
- **복구 checkpoint**: 이전 실패 verification이 통과하고 마지막 verified checkpoint 이후 tracked 변경이 있을 때 C2 checkpoint를 만든다. no-op repair는 ledger에 사유를 기록하고 중복 commit을 만들지 않는다.
- **Host 운영 기록**: host adapter는 transport와 worker 결과를 제공하고 ForgeFlow Lifecycle State Schema 2가 attempt counter, fencing, retry/transition guard를 durable하게 기록한다. Host transient output은 canonical evidence가 아니다.
- **5회 차단 규칙**: no-progress 1~4회는 host가 remediation과 재검증을 계속한다. 정확히 5회가 누적된 경우에는 사용자 또는 승인 authority의 결정을 요청하고 그 근거를 release artifact에 기록한다. 단순 turn 종료나 agent failure는 blocker 증적이 아니다.

### Loop 3: 아키텍처/명세 회귀 루프 (Architecture Regression Loop)
- **트리거**: Loop 2 서킷 브레이커 발동, 또는 구현 도중 기술적 불가성/기획 결함 확인 시.
- **서킷 브레이커**: 동일 Task당 최대 2회 회귀 제한. 전체 누적 수정 시도 상한(Total Fix Budget: 8회) 초과 시 Task 폐기 및 전면 재기획.
- **Resume rule**: host는 authority resolution 또는 새 remediation evidence를 QA artifact에 기록한 뒤 작업을 재개한다. evidence harness는 그 결과를 검사하고 next action을 보고할 뿐 host의 재개를 수행하지 않는다.

### Host orchestration and evidence boundary

- ForgeFlow는 durable lifecycle control state, transition/completion guard와 canonical evidence를 소유한다. implementation/review/command의 transport, worker 실행, wait, cancellation과 runtime result는 host adapter가 소유한다. ForgeFlow는 host-specific session semantics를 추론하지 않는다.
- host가 얻은 durable Gate/reviewer/artifact/verification evidence는 canonical release artifact에 기록한다. rejected 또는 failed evidence는 forward completion이 아니라 unmet condition과 remediation `next_action`을 만든다.
- `RELEASE_NOTES.md`는 사용자용 release communication artifact다. Gate 2 뒤 `PACKAGE_FINALIZATION`에서 정리할 수 있고, 존재하면 Gate 3 package manifest에 포함된다. Release Notes-only 수정은 Gate 2 QA evidence를 stale 처리하지 않지만 Gate 3 manifest는 새 digest로 재승인해야 한다.
- strict audit은 one evidence snapshot을 검사한다. malformed/unsafe/stale/candidate-mismatched evidence는 fail-closed이며, audit output은 host의 실행 상태 또는 자연어 approval을 증거로 사용하지 않는다.

### Selectable autonomous delegation

- `interactive`가 기본값이며 사람과 lifecycle owner의 판단 교환을 유지한다.
- `autonomous` 선택·활성화·운영 자체는 Tier를 올리거나 내리는 risk signal이 아니다. Tier와 Gate 강도는 요청의 실제 변경과 기존 risk signal만으로 분류하며, 모든 Tier(Tier 1/2/3)에서 `interactive`와 `autonomous`를 직교적으로 선택할 수 있다.
- **로컬 단일 에이전트 Attestation 완전 면제**: 로컬 단일 에이전트(LLM-in-the-loop) 환경에서는 암호학적 HMAC 서명 증명(`ActivationAttestation`), nonce CAS, verifier proof가 완전히 면제된다. 파일 시스템 기반의 `control.loop_record`를 유지하여 시도 횟수, no-progress 카운터, failure fingerprint, 정형화된 remediation 목록을 영속화한다.
- 고신뢰 control-plane(HMAC attestation, nonce CAS, concurrency fencing)은 다중 분산 컨트롤러, 원격 배포 또는 고위험 확장이 요구될 때만 조건부(`--high-assurance`)로 강제한다.
- **자율 완결 루프 보장**: 사용자의 "계속", "진행", "수정", "해줘" 등 작업 지시는 자율 완결 위임으로 간주한다. 에이전트가 대화형 상태에 머물러 턴을 조기 종료하는 것을 금지하며, Gate 2 Sign-off까지 Loop 2 자가 치유를 완결한다. `Go`와 `계속`은 이미 활성화된 autonomous lifecycle의 재개 신호로도 동작하며, dormant lifecycle인 경우라도 사용자가 작업을 요청했다면 즉시 autonomous 완결 루프를 가동한다.
- **과거 산출물 격리**: 과거 릴리즈 산출물(`tasks/completed/` 및 과거 `docs/releases/` 아카이브)은 정적 감사 증적일 뿐 행동 지침이 아니다. 에이전트는 규칙/지침 판단을 위해 이를 참조하거나 인용해서는 안 되며, 오직 `docs/spec/`, `docs/forgeflow/GOVERNANCE.md`, 또는 `AGENTS.md`만을 단일 진실 공급원으로 삼는다.
- autonomous lifecycle owner는 internal work를 dispatch한 뒤 완료 또는 attention까지 wait하고, 결과를 evaluate하며, self-resolvable failure를 remediation으로 전환한다. 미해결 지적사항(unresolved remediation)이 남아 있으면 final response를 내지 않는다. evidence completion 또는 authority boundary만 정상 종료점이다.
- autonomous lifecycle owner의 stage-owner, implementer, reviewer 배치는 portable operating guidance다. physical nesting, role assignment, parent 관계와 runtime result transport는 host 책임이며, lifecycle stage/status와 completion guard는 ForgeFlow state가 정본이다.
- scope, risk, credential, destructive operation, remote Git, publish, deploy, product/design decision과 동일 failure fingerprint 누적 5회의 authority boundary는 기존 lifecycle 규칙을 따른다. explicit autonomous lifecycle은 `.forgeflow/lifecycle/<release-id>.json`이 필요하고, legacy evidence-only release는 state 없이 interactive로 유지된다. v0.6은 QA Evidence v2, Release Sign-off, package manifest와 state seal을 함께 enforce한다.

#### 자율 오케스트레이션 4단계 불변 루프 (4-Step Invariant Autonomous Loop)

모든 자율 실행 수명주기는 다음 4단계 불변 루프를 강제한다:
1. **Step 1 (Dispatch)**:
   - 메인 에이전트(Supervisor)는 작업 단위를 식별하고, 격리 워커 또는 전문 서브에이전트에 명확한 파일 경로 및 목표를 할당하여 구현을 실행한다.
2. **Step 2 (Verify)**:
   - 자동 단위/통합 테스트 및 하네스 감사(`forgeflow check`)를 실행하여 증적을 수집한다.
3. **Step 3 (Evaluate & Remediate)**:
   - **검증 실패 또는 리뷰 REJECT 발생 시**:
     - 실패 메시지에서 비결정론적 요소(타임스탬프, UUID, 임시 경로, 메모리 주소)를 마스킹하여 결정론적 `failure_fingerprint`를 산출한다.
     - `control.loop_record`에 기록하고, 동일 fingerprint가 5회 미만이면 **사용자 개입 없이 즉시 Step 1으로 자가 수정(Loop 2) 재전입**한다.
     - 동일 fingerprint가 5회에 도달하면 서킷 브레이커를 발동(`terminal_reason="circuit-breaker"`), 상태를 `BLOCKED`로 전이하고 사용자 지시를 대기한다.
   - **검증 성공 시**: 다음 Gate 또는 스테이지로 자동 전진한다.
4. **Step 4 (Completion Guard)**:
   - Gate 2 QA Sign-off 시 모든 remediation 항목이 `status="RESOLVED"`로 종결되었는지 `completion_ready()`로 기계적 검증한다. 미해결 결함(`OPEN`)이 남아있으면 최종 응답을 종료할 수 없다.

#### 진짜 멈춤 vs 가짜 멈춤 표준 체크리스트 (True vs False Stopping Conditions)

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

#### Supervisor-Worker 다중 에이전트 협업 규범

- **Supervisor (메인 에이전트)**:
  - 수명주기 상태 기계(`LifecycleStore`), 증적 장부(`loop_record`), 루프 예산(5회 한도), Git 커밋 충돌 방지를 총괄한다.
  - 직접 구현 코드를 대량 수정하지 않고 워커 에이전트의 결과를 취합·검증·심사 배치한다.
- **Worker (서브에이전트)**:
  - 독립된 도메인(예: Reliability 관점의 통신/복구, Maintainability 관점의 RTM/픽스처, Security 관점의 권한/검증)별로 파일 경로를 격리(`File-Path Partitioning`)하여 수정을 수행한다.
  - 동시 쓰기로 인한 Git 충돌 방지를 위해 Supervisor가 순차 병합(Serialized Staging)을 통제한다.

---

## 4. 롤백 및 실패 복구 표준 프로토콜 (Rollback Protocol)

1. **Git 형상 롤백**: Task 중단/폐기 시 생성된 작업 브랜치는 폐기하고 메인 브랜치로 안전하게 복귀.
2. **워크스페이스 정리 (Purge)**: `workspaces/task-<release-id>/` 하위 불완전 소스 및 임시 산출물 일괄 정리.
3. **프로세스 및 포트 클린업**: 테스트 실행 중 점유된 백그라운드 프로세스 및 포트 즉시 Kill.
4. **checkpoint 복구**: 실패 또는 중단 시 immutable recovery snapshot을 먼저 보존하고, 최신 verified SHA에서 새 recovery branch를 만든다. 원 branch와 snapshot은 retention decision 전까지 유지한다. 변경을 버리는 reset/clean/checkout 또는 branch 삭제는 승인자·대상 SHA·사유·시각·snapshot integrity·retention 결정을 ledger에 기록한 명시적 승인 없이는 수행할 수 없다.
