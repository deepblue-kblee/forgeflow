# 🔗 GitHub Spec Kit 주입 규범 및 훅 통합 아키텍처 (SPECKIT_HOOKS_AND_NORMS.md)

이 문서는 ForgeFlow 프레임워크가 **GitHub Spec Kit**의 대화형 실행 엔진 위에 엔터프라이즈 하네스 거버넌스(Harness Governance)를 주입하는 **3대 메커니즘, 전체 훅(Hook) 라이프사이클, 체크포인트 커밋 규범, 피쳐 브랜치 수명주기**를 상세히 규정하는 공식 표준 설명서이다.

---

## 제1장. 이중 엔진 결합 및 3대 거버넌스 주입 메커니즘

순정(Vanilla) GitHub Spec Kit은 뛰어난 대화형 인터뷰와 명세 작성 능력을 제공하지만, 게이트 통제, 품질 감사, 상태 격리, 체크포인트 커밋에 대한 규범이 부재하여 에이전트의 즉흥적 행동("Vibe Coding")을 통제하기 어렵다.
ForgeFlow는 Spec Kit 자체의 코드를 변형하지 않고, Spec Kit이 공식 지원하는 **3대 확장 통로**를 통해 엔터프라이즈 규범을 100% 주입한다.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        GitHub Spec Kit (실행 엔진)                      │
│                                                                        │
│  [1. 정책 헌법] .specify/memory/constitution.md (모든 명령 시작 전 최우선 로드)   │
│  [2. 강제 훅]   .specify/extensions.yml        (단계 진입 전 물리적 차단 Fail-Closed)│
│  [3. 템플릿]    .specify/templates/commands/   (프롬프트 레벨 체크리스트 오버라이드)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 거버넌스 통제 및 결속
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         ForgeFlow (거버넌스 엔진)                       │
│                                                                        │
│  - Gate 1: 명세 승인 (GATE1_REVIEW.md)                                  │
│  - Gate 2: QA 품질 승인 (QA_SIGNOFF.md, QA 커밋 SHA 바인딩)            │
│  - Gate 3: 릴리즈 승인 및 패키지 밀봉 (RELEASE_SIGNOFF.md)              │
│  - 릴리즈 수명주기 보관소 (tasks/in-progress/ ➔ tasks/completed/)       │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.1 통로 1: 정책 헌법 주입 (`.specify/memory/constitution.md`)
- Spec Kit 공식 스펙상 모든 명령어(`/speckit-specify`, `/speckit-plan`, `/speckit-implement` 등)는 실행 전 이 문서를 최우선 메모리로 로드한다.
- ForgeFlow는 이 파일에 5대 불변 헌법을 선언하여 에이전트의 사고와 행동을 구속한다.

### 1.2 통로 2: 필수 강제 실행 훅 주입 (`.specify/extensions.yml`)
- Spec Kit의 확장 훅 아키텍처에서 `optional: false`로 등록된 훅은 에이전트가 본문을 실행하기 전에 **"반드시 실제로 실행하고 대기(MUST actually invoke the hook and wait for it to finish)"**해야 한다.
- ForgeFlow는 `before_implement`에 `forgeflow check --stage 2`를 주입하여, Gate 1 미승인 시 종료 코드 `exit 1`로 셸 레벨에서 물리적으로 코드 작성을 사전 차단(Fail-Closed)한다.

### 1.3 통로 3: 프롬프트 템플릿 오버라이드 (`.specify/templates/commands/*.md`)
- Spec Kit은 로컬 프로젝트의 `.specify/templates/commands/` 디렉터리에 동명 마크다운 템플릿이 존재하면 이를 기본 내장 템플릿 대신 최우선 로드한다.
- ForgeFlow는 `implement.md`의 `## Pre-Execution Checks`에 게이트 유효성 검사 및 자가 치유(Loop 2) 가이드라인을 주입한다.

---

## 제2장. Spec Kit 훅 라이프사이클 및 커밋 매핑 매트릭스

Spec Kit 공식 지원 훅은 커맨드 단위의 **사전 훅(`before_*`)**과 **사후 훅(`after_*`)**으로 구성된다.

### 2.1 전체 훅 라이프사이클 일람표

| Spec Kit 훅 포인트 | 실행 시점 | ForgeFlow 거버넌스 바인딩 | 권장 동작 및 커밋 매핑 |
| :--- | :--- | :--- | :--- |
| `hooks.before_specify` | `/speckit.specify` 시작 직전 | 피쳐 브랜치 생성 및 환경 확인 | `create-new-feature.sh` (브랜치 분기) |
| `hooks.after_specify` | `/speckit.specify` 명세 완료 후 | Stage 1 완료 점검 | 선택적 스펙 커밋 (`docs: specify ...`) |
| `hooks.before_clarify` | `/speckit.clarify` 모호성 질문 전 | 명세서 존재 확인 | 환경 검증 |
| `hooks.after_clarify` | `/speckit.clarify` 인터뷰 완료 후 | Gate 1 준비 상태 확인 | 명세 확정 커밋 |
| `hooks.before_plan` | `/speckit.plan` 설계 시작 직전 | Gate 1 승인 증적 확인 | 검증 훅 (`forgeflow check --stage 2`) |
| `hooks.after_plan` | `/speckit.plan` 아키텍처 완료 후 | 설계 일관성 확인 | 설계 커밋 (`docs: plan ...`) |
| `hooks.before_tasks` | `/speckit.tasks` 분해 시작 직전 | `plan.md` 유효성 검증 | 설계 산출물 검증 |
| `hooks.after_tasks` | `/speckit.tasks` 분해 완료 후 | Stage 2 종료 및 체크포인트 2 | **체크포인트 2 커밋** (`docs: tasks ...`) |
| `hooks.before_implement` | `/speckit.implement` 코드 작성 직전 | **Gate 1 승인 증적 물리적 차단** | `forgeflow check --stage 2 --quiet` (필수) |
| `hooks.after_implement` | `/speckit.implement` 모든 태스크 종료 후 | Stage 3 종료 및 Gate 2 진입 준비 | **체크포인트 4 커밋 / QA Sign-Off 결속** |

### 2.2 거시 훅(Macro Hook) vs 미시 체크포인트(Micro Checkpoint)의 역할 분담

> [!IMPORTANT]
> **Spec Kit의 구조적 한계와 해결책**:
> Spec Kit의 훅 시스템은 커맨드 전/후(`before_implement`, `after_implement`) 레벨에서만 트리거되며, `/speckit.implement` 내부에서 `tasks.md`의 개별 태스크(`Task 1.1`, `Task 1.2` 등)가 실행될 때마다 발동하는 마이크로 훅(`after_task`)을 기본 지원하지 않는다.
>
> 따라서:
> 1. **거시적 단계 제어 (Macro)**: `extensions.yml`의 공식 훅(`before_implement` 게이트키퍼, `after_implement` QA 준비)을 통해 기계적으로 제어한다.
> 2. **미시적 TDD 체크포인트 (Micro)**: 헌법(`.specify/memory/constitution.md`) 제3조 및 `implement.md` 템플릿 지침을 통해 **"개별 태스크(`Task N.N`)가 테스트를 통과할 때마다 원자적 체크포인트 커밋을 생성하라"**고 에이전트에게 행동 규범으로 주입한다.

---

## 제3장. 피쳐 브랜치 수명주기 및 4대 마일스톤 체크포인트 규범

시스템은 작업 중인 코드가 불완전한 상태에서 `main` 브랜치를 오염시키는 것을 방지하기 위해 **완전한 브랜치 격리 수명주기**를 준수한다.

```text
[main 브랜치] (항상 안정적이며 배포 가능한 클린 상태)
   │
   ├─► 1. 격리 분기: git checkout -b feat/<release-id>
   │      │
   │      ├─ 📌 [체크포인트 1] Gate 1 명세 승인 완료 시점
   │      │     산출물: tasks/in-progress/<id>/spec.md + GATE1_REVIEW.md
   │      │     커밋: git commit -m "docs: establish spec and gate 1 approval (<id>)"
   │      │
   │      ├─ 📌 [체크포인트 2] Stage 2 기술 설계 및 태스크 분해 완료 시점
   │      │     산출물: plan.md + tasks.md
   │      │     커밋: git commit -m "docs: establish plan and tasks breakdown (<id>)"
   │      │
   │      ├─ 📌 [체크포인트 3] Stage 3 구현 진행 - TDD 원자적 태스크 완수 시마다
   │      │     - Task 1.1 구현 + 테스트 통과 ➔ commit -m "feat(core): implement task 1.1 (<id>)"
   │      │     - Task 1.2 구현 + 테스트 통과 ➔ commit -m "test: add integration test 1.2 (<id>)"
   │      │     - ※ 구현 중 에러 발생 시: 이전 정상 태스크 체크포인트로 안전하게 git rollback!
   │      │
   │      ├─ 📌 [체크포인트 4] Gate 2 QA 품질 승인 완료 시점
   │      │     산출물: QA_SIGNOFF.md (review --strict 통과, 전체 테스트 100% Pass)
   │      │     커밋: git commit -m "chore(qa): sign off gate 2 qa verification (<id>)"
   │      │     ★ 이 시점의 Commit SHA가 QA-SHA로 영구 결속됨
   │      │
   │      └─ 📌 [Gate 3 릴리즈 승인] 패키지 밀봉
   │            산출물: RELEASE_SIGNOFF.md + tasks/completed/ 이동
   │            커밋: git commit -m "release: seal <id> package"
   │      │
   ▼      ▼
[main 브랜치 복귀]
   │
   ├─► 2. 머지: git checkout main && git merge feat/<release-id>
   └─► 3. 정리: git branch -d feat/<release-id> (Fast-Path Close)
```

### 3.1 체크포인트 커밋의 3대 안전 규칙
1. **Never Commit Red**: 단위/통합 테스트가 실패 중인 중간 상태는 절대로 git commit하지 않는다.
2. **Commit Clean Green**: `tasks.md`의 특정 태스크와 관련 테스트가 100% 통과하여 안전한 상태가 되었을 때만 원자적 커밋을 생성한다.
3. **Safe Rollback Point**: 새로운 태스크 구현 중 코드가 심각하게 꼬이거나 아키텍처 결함이 발생하면, 즉시 `git reset --hard HEAD` 또는 직전 정상 태스크 커밋으로 롤백하여 깨끗한 상태에서 자율 치유(Loop 2/3)를 재시도한다.

---

## 제4장. 5대 불변 거버넌스 헌법 조항 전문

이 조항은 타깃 프로젝트의 [`.specify/memory/constitution.md`](file:///.specify/memory/constitution.md)에 상주하여 에이전트의 모든 작업을 법적으로 구속한다.

```markdown
# Project Constitution: Hybrid Governance Rules

## 제1조 (무승인 구현 금지 - No Code Before Gate 1)
어떠한 에이전트도 `tasks/in-progress/<id>/GATE1_REVIEW.md`의 공식 승인(APPROVED) 증적이 
존재하지 않는 상태에서 `src/**` 경로에 신규 소스 코드를 생성하거나 기존 코드를 수정할 수 없다. 
`/speckit.implement`가 호출되더라도 이 원칙이 최우선하며, 위반 시 즉시 실행을 중단하고 사용자에게 보고해야 한다.

## 제2조 (가짜 멈춤 금지 - No False Stopping)
구현 중 발생하는 단순 단위 테스트 실패, 린트 오류, 사소한 컴파일 에러는 사용자에게 턴을 넘기거나 
작업을 종료할 수 있는 사유가 아니다. 에이전트는 결함 원인을 스스로 분석하고 코드를 수정하는 
내부 자가 치유 루프(Loop 2)를 자율적으로 완주해야 한다.

## 제3조 (원자적 루프 및 체크포인트 정의 - Atomic Remediation & Checkpoints)
자가 치유의 1회 루프는 반드시 `결함 원인 식별 → 코드/테스트 수정 → 테스트 재실행`의 단위를 거치며, 
실패 상태의 불완전한 코드를 커밋하는 행위를 엄격히 금지한다. 에이전트는 `tasks.md`의 개별 태스크와 
테스트가 100% 정상 통과(Green)한 시점에만 원자적 체크포인트 커밋을 생성하여 롤백 안전망을 확보한다.

## 제4조 (루프 예산 및 진짜 멈춤 - Loop Budget & True Stop)
동일한 에러 핑거프린트로 5회 연속 코드 수정 및 테스트 통과에 실패한 경우에만 작업을 즉시 중지하고 
사용자에게 에스컬레이션(진짜 멈춤)한다.

## 제5조 (스펙 무단 하향 금지 - No Spec Downgrade)
구현의 어려움을 이유로 사용자 승인 없이 `spec.md`의 요구사항이나 Acceptance Criteria를 
축소·삭제·완화할 수 없다. 스펙 수정이 필요한 경우 반드시 공식 스펙 회귀(Loop 3) 절차를 거쳐 
Gate 1 재승인을 획득해야 한다.
```

---

## 제5장. 실전 설정 파일 템플릿

### 5.1 `.specify/extensions.yml`
```yaml
version: "1.0"
hooks:
  before_implement:
    - extension: forgeflow-gatekeeper
      command: forgeflow check --stage 2 --quiet
      optional: false
      prompt: "ForgeFlow Gate 1 승인 증적(GATE1_REVIEW.md)의 유효성을 기계적으로 검증한다. 미승인 시 소스 코드 수정을 즉시 물리적으로 차단한다."
  after_implement:
    - extension: forgeflow-qa-precheck
      command: forgeflow review --strict --quiet
      optional: true
      prompt: "구현 완료 후 정적 분석 및 복잡도 임계치를 검증하여 Gate 2 QA Sign-Off를 준비한다."
```

### 5.2 `.specify/templates/commands/implement.md`
```markdown
---
description: Execute task implementation with Gate 1 enforcement and autonomous healing loop
---

## Pre-Execution Checks
1. Gate 1 Approval: Verify `tasks/in-progress/<release-id>/GATE1_REVIEW.md` exists with status `APPROVED`.
2. Workspace Isolation: Verify work is being conducted on branch `feat/<release-id>`.

## Implementation Directives
- Follow `tasks.md` sequentially in TDD fashion.
- Inner Loop (Loop 2): Autonomously analyze, fix, and re-test without stopping on failures (budget: 5 attempts).
- Checkpoint Commits: Create a clean git commit each time a discrete task (`- [ ] Task N.N`) and its tests 100% pass.
- Rollback: If code becomes corrupted during remediation, revert to the last clean task checkpoint.
```
