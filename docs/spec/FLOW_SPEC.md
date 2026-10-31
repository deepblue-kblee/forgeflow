# ForgeFlow-SpecKit 하이브리드 워크플로우 상세설계서 (Draft v1.0)

---

## 제1장. 개요 및 설계 원칙

### 1.1 배경 및 목적
인공지능 코딩 에이전트(LLM Agent)를 활용한 소프트웨어 개발에서 즉흥적인 프롬프트 작성("Vibe Coding")은 아키텍처 드리프트, 검증 누락, 환각 코딩을 유발한다. 반면, 지나치게 무거운 거버넌스 문서를 프로젝트 내부에 직접 배포하는 방식은 레거시 문서 오염, 경로 불일치, 컨텍스트 토큰 낭비를 초래한다.

본 상세설계서는 **GitHub Spec Kit**의 우수한 대화형 명세 기반 개발(Spec-Driven Development) 실행력과 **ForgeFlow**의 엔터프라이즈 하네스 거버넌스(Harness Governance) 통제력을 유기적으로 결합한 하이브리드 개발 파이프라인을 규정한다.

### 1.2 이중 엔진 아키텍처 (Dual-Engine Architecture)
본 시스템은 실행과 통제를 물리적·논리적으로 분리하는 이중 엔진 모델을 채택한다.

1. **실행 엔진 (Worker / Micro-Execution Engine) — GitHub Spec Kit**:
   - 에이전트와 사용자 간의 대화형 인터뷰를 통해 요구사항을 발굴한다.
   - 명세서(`spec.md`), 아키텍처 계획(`plan.md`), 원자적 태스크(`tasks.md`)를 작성하고 순차적 TDD 구현을 주도한다.
2. **거버넌스 엔진 (Supervisor / Macro-Governance Harness) — ForgeFlow**:
   - 릴리즈 패키지 단위(`tasks/in-progress/<release-id>`)의 수명주기 상태 기계를 관리한다.
   - 명세 승인(Gate 1), QA 품질 승인(Gate 2), 패키지 밀봉 및 릴리즈 승인(Gate 3)을 기계적으로 차단 및 승격한다.
   - 테스트 커버리지, 골든 픽스처(QE-xx), 정적 분석(Strict Review), 커밋 SHA 무결성을 불변 장부로 바인딩한다.

### 1.3 핵심 설계 원칙
- **Zero-Dependency 원칙**: 거버넌스 코어와 검증 CLI는 외부 의존성 없이 Python 3.10+ 표준 라이브러리만으로 100% 동작한다.
- **Fail-Closed Gatekeeper 원칙**: 게이트 승인 증적이 누락되었거나 검증이 실패한 경우, 어떠한 하위 단계로의 진행도 물리적으로 차단한다.
- **Progressive Disclosure 원칙**: 에이전트에게 한 번에 방대한 프레임워크 문서를 주입하지 않고, 현재 단계에 필요한 스킬과 지침만 점진적으로 노출한다.
- **Atomic Remediation Loop 원칙**: 구현 단계에서 단순한 테스트 실패는 중단 사유가 아니며, `결함 식별 → 코드 수정 → 테스트 성공 → git commit` 단위를 자율 완수한다.

---

## 제2장. 시스템 구성 및 디렉터리 아키텍처

### 2.1 프로젝트 저장소 레이아웃
타겟 프로젝트 저장소에는 복잡한 스펙 문서나 프레임워크 코어를 두지 않으며, 오직 진행 중인 릴리즈 패키지만 유지한다.

```text
<project-root>/
├── .forgeflow.json                     # 프로젝트 전역 거버넌스 설정
├── .specify/                           # Spec Kit 환경 설정
│   ├── memory/
│   │   └── constitution.md             # [최상위 헌법] 게이트 통과 전 구현 금지, 루프 규범
│   ├── templates/                      # 사전 검사 훅이 주입된 로컬 템플릿 오버라이드
│   │   └── commands/
│   │       ├── specify.md
│   │       ├── clarify.md
│   │       ├── plan.md
│   │       ├── tasks.md
│   │       └── implement.md            # Gate 1 검증 및 자가 치유 규범 주입
│   ├── extensions.yml                  # Spec Kit 공식 확장 및 강제 훅 정의
│   └── feature.json                    # 현재 활성 릴리즈/피쳐 상태 추적기
│
├── tasks/                              # ForgeFlow 릴리즈 패키지 수명주기 보관소
│   ├── in-progress/
│   │   └── v0.1.0-cache-engine/        # 단일 활성 릴리즈 패키지
│   │       ├── spec.md                 # [Spec Kit] 기능 요구사항 및 대화 결정사항
│   │       ├── GATE1_REVIEW.md         # [ForgeFlow] Gate 1 명세 승인 증적
│   │       ├── plan.md                 # [Spec Kit] 기술 아키텍처 및 데이터 모델
│   │       ├── tasks.md                # [Spec Kit] 의존성 순서의 원자적 태스크 목록
│   │       ├── QA_SIGNOFF.md           # [ForgeFlow] Gate 2 QA 승인 증적 (SHA 바인딩)
│   │       └── RELEASE_SIGNOFF.md      # [ForgeFlow] Gate 3 릴리즈 승인 및 머지 준비
│   └── completed/
│       └── v0.1.1-query-engine/        # [ForgeFlow] 밀봉(Seal)된 과거 완료 패키지
└── src/ ...                            # 실제 프로젝트 소스 코드
```

### 2.2 설정 파일 규격

#### 1. `.forgeflow.json`
```json
{
  "forgeflow_version": "0.1.0",
  "governance": {
    "tasks_dir": "tasks",
    "strict_mode": true,
    "max_loop_budget": 5,
    "test_timeout_seconds": 60,
    "auto_create_branch": false
  },
  "paths": {
    "in_progress": "tasks/in-progress",
    "completed": "tasks/completed"
  }
}
```
- `test_timeout_seconds` (선택, 기본값 60초): `RuntimeTestRunner`의 단위/회귀 테스트 실행 타임아웃(초). 대규모 회귀 테스트 스위트를 보유한 프로젝트에서 가짜 타임아웃을 방지하기 위해 프로젝트 레벨에서 상향 조정할 수 있으며, 비정상 값(불리언, 비숫자, 음수, 0, 무한대) 지정 시 엄격히 거부된다.
- `auto_create_branch` (선택, 기본값 `false`): Stage 3 격리 구현 진입 시 `feat/<release-id>` 브랜치 자동 분기 여부. `false`(기본값)인 경우 worktree 환경과의 충돌을 방지하기 위해 별도 브랜치 자동 생성을 생략하고 현재 브랜치/worktree에서 작업을 진행한다. 사용자가 CLI에서 `--create-branch`를 명시하거나 직접 요청하면 브랜치가 생성된다. 향후 프로젝트 전역에서 브랜치 생성을 기본 동작으로 삼고자 할 때 `AGENTS.md` 같은 지침 문서를 오염시키지 않고 본 설정(`auto_create_branch: true`)을 단일 진실 공급원(SSOT)으로 사용한다.

#### 2. `.specify/extensions.yml`
Spec Kit의 공식 확장 훅 규격을 사용하여 구현 시작 전 Gate 1 통과 여부를 기계적으로 검증한다.
```yaml
version: "1.0"
hooks:
  before_implement:
    - extension: forgeflow-gatekeeper
      command: forgeflow check --stage 2 --quiet
      optional: false
      prompt: "ForgeFlow Gate 1 승인 증적(GATE1_REVIEW.md)의 유효성을 검증한다. 미승인 시 즉시 중단한다."
```

### 2.3 Spec Kit 공식 규범 주입(Governance Injection) 아키텍처

순정 Spec Kit은 실패 시 즉각 중단(HALT)하는 단순 실행기이므로, ForgeFlow의 엔터프라이즈 거버넌스와 자가 치유 규범을 주입하기 위해 Spec Kit이 표준으로 제공하는 3대 공식 확장 메커니즘을 결합한다.

#### 1. 정책 헌법 시스템 (`.specify/memory/constitution.md`)
Spec Kit 공식 스펙상 모든 커맨드(`/specify`, `/plan`, `/implement` 등)는 실행 전 이 문서를 최우선 메모리로 로드한다. 하이브리드 아키텍처에서는 본 파일에 다음 4대 불변 거버넌스 헌법을 선언하여 에이전트의 행동을 법적으로 구속한다.

```markdown
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
```

#### 2. 필수 강제 실행 훅 (`extensions.yml` Mandatory Hook)
Spec Kit의 `templates/commands/implement.md` 공식 스펙(27~58행)은 `optional: false`로 등록된 훅을 에이전트가 본문을 실행하기 전에 **"반드시 실제로 실행하고 대기(MUST actually invoke the hook and wait for it to finish)"**하도록 규정한다.
- **물리적 차단 원리**: `forgeflow check --stage 2` 명령이 Gate 1 미승인 시 종료 코드 `exit 1`을 반환하므로, 셸 스크립트 레벨에서 실행 자체가 에러로 종결되어 코드를 작성할 틈을 주지 않고 물리적으로 차단(Fail-Closed)한다.

#### 3. 공식 프리셋 및 로컬 템플릿 오버라이드 (`Presets & Overrides`)
Spec Kit은 `specify preset add <preset-name>` 및 로컬 `.specify/templates/commands/implement.md` 오버라이드 아키텍처를 공식 지원한다.
- 템플릿 상단의 `## Pre-Execution Checks`에 게이트 유효성 검사 절차를 1번 지침으로 명시하여, 프롬프트 레벨에서도 이중으로 가로채기를 보장한다.

### 2.4 전역 런타임 업그레이드 및 로컬 사양 동기화 (`upgrade` & `update`)

ForgeFlow 환경의 장기적 유지보수와 복수 프로젝트 간 일관성을 위해 2단계 대칭 CLI 구조와 스마트 파사드를 제공한다:

1. **전역 런타임 판올림 (`forgeflow upgrade`)**:
   - `forgeflow upgrade --check`: 무설치 버전 비교 검사 (원격 최신 릴리즈와 로컬 비교).
   - `forgeflow upgrade`: 원격 최신 버전을 다운로드하여 OS 전역 런타임(`~/.local/forgeflow`), CLI 바이너리, 및 `~/.agents/skills/`를 최신으로 승격.
2. **로컬 리포지토리 거버넌스 사양 동기화 (`forgeflow update`)**:
   - 현재 작업 프로젝트의 `.forgeflow.json`, `.specify/scripts/bash/`(0o755 권한 보장), 템플릿, 헌법을 현재 설치된 ForgeFlow 규격으로 갱신.
   - `tasks/in-progress/` 및 `tasks/completed/`의 사용자 작업 데이터는 100% 온전히 보존.
3. **스마트 파사드 스킬 (`/update-forgeflow`)**:
   - 에이전트 환경에서 한 번의 명령으로 전역 `upgrade` 후 로컬 `update`를 순차 수행하여 개발 편의성을 극대화.

---


## 제3장. 엔드투엔드 워크플로우 상세 설계

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Stage 1: 기획 & 명세 작성                                                             │
│   /speckit.specify (의도 입력 및 Triage) ──► /speckit.clarify (대화형 질문/답변)       │
│   ──► tasks/in-progress/<id>/spec.md 생성                                              │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Gate 1: 명세 승인 (Spec Sign-Off) ★ Gate 1 승인 관문                                    │
│   Risk Tiering (Tier 1/2/3) ──► GATE1_REVIEW.md 발행 및 "APPROVED" 확정                │
│   * 미승인 시 이후 구현 단계 물리적 실행 차단 (Fail-Closed)                            │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Stage 2: 기술 설계 & 태스크 분해                                                       │
│   /speckit.plan (아키텍처/데이터모델) ──► /speckit.tasks (원자적 체크리스트 도출)       │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Stage 3: 격리 구현 & 자가 치유 루프                                                    │
│   /speckit.implement ──► [Pre-Hook: Gate 1 검증] ──► 순차 구현 및 TDD                  │
│     ├── Inner Loop (Loop 2): 테스트 실패 시 수정-테스트-커밋 자율 완수 (최대 5회)       │
│     └── Outer Loop (Loop 3): 스펙 모순 발생 시 spec.md 수정 및 Gate 1 재승인 회귀      │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Gate 2: QA 품질 승인 (QA Sign-Off) ★ Gate 2 승인 관문                                   │
│   forgeflow review --strict ──► 100% Tests Pass ──► QA_SIGNOFF.md 발행 및 APPROVED     │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Gate 3: 릴리즈 승인 & 패키지 밀봉 (Release Sign-Off) ★ Gate 3 승인 관문                 │
│   사용자 Go/No-Go 최종 승인 ──► RELEASE_SIGNOFF.md ──► tasks/completed/ 패키지 밀봉   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Stage 1: 기획 및 스펙 명확화 (Planning & Clarification)
1. **진입 및 명세 초안 작성 (`/speckit.specify`)**:
   - 사용자가 한 줄의 자연어 의도를 입력한다.
   - Spec Kit 엔진은 `spec-template.md`를 기반으로 `spec.md` 초안 파일을 생성한다.
   - 에이전트는 즉시 요구사항의 복잡도를 측정하여 일반 피쳐와 에픽(Spec of Specs) 규모를 판정한다.
2. **대화형 인터뷰 (`/speckit.clarify`)**:
   - 에이전트는 `spec.md`의 모호성(Ambiguity)을 스캔하여 권장 선택지(A/B)를 포함한 최대 5개의 질문을 제시한다.
   - 사용자의 결정은 `spec.md` 파일의 `## Clarifications` 섹션에 불변 기록으로 저장되며, 본문 요구사항이 동기화된다.
3. **단계 종료 조건**:
   - `spec.md`에 모호한 지점이 없으며, Acceptance Criteria가 명확히 기술된 상태.
   - Gate 1 승인 단계로 전이한다.

### 3.2 Gate 1: 명세 승인 (Specification Sign-Off)
1. **심사 및 승인 절차**:
   - ForgeFlow 엔진 및 에이전트는 `spec.md`의 변경 범위와 아키텍처 영향을 평가하여 리스크 티어를 동적 분류한다:
     - **Tier 1 (Minor)**: 인터페이스 변경 없는 국소 버그 수정/문서. AI 자체 승인(Self-Review).
     - **Tier 2 (Standard)**: 일반 신규 기능. 독립 시니어 리뷰어 1인 정밀 심사.
     - **Tier 3 (Core/Arch)**: 보안, 인증, 데이터 모델, 거버넌스 제어 평면 변경. 3인 독립 패널(보안, 안정성, 유지보수성) 병렬 심사 및 사용자 구두 승인 필수.
2. **승인 산출물 (`GATE1_REVIEW.md`) 확정**:
   - 심사 통과 시 `tasks/in-progress/<release-id>/GATE1_REVIEW.md`에 `Gate 1 Verdict: APPROVED`가 확정 기록된다.
   - 격리 작업 브랜치(`feat/<release-id>`) 생성 및 후속 기술 설계/구현 착수가 잠금 해제된다.

### 3.3 Stage 2: 기술 설계 및 태스크 분해 (Architecture & Breakdown)
1. **기술 아키텍처 수립 (`/speckit.plan`)**:
   - 승인된 `spec.md`를 바탕으로 모듈 인터페이스, 에러 처리 규격, 데이터 스키마를 기술한 `plan.md`를 생성한다.
2. **원자적 태스크 분해 (`/speckit.tasks`)**:
   - `plan.md`의 설계를 15개 내외의 실행 단위로 쪼개어 `tasks.md`를 생성한다.
   - 단계는 `Setup` ──► `Tests` ──► `Core` ──► `Integration` ──► `Polish` 순서를 강제한다.
3. **단계 종료 조건**:
   - `tasks.md`의 의존성 정렬 완료 및 네비게이터의 "다음 명령: `/speckit.implement`" 출력.

### 3.4 Stage 3: 격리 구현 및 자가 치유 루프 (Isolated Implementation & Self-Healing)
1. **사전 검사(Pre-Execution Checks)에 의한 게이트 가로채기**:
   - `/speckit.implement`가 호출되면 `.specify/extensions.yml`의 `hooks.before_implement`가 트리거된다.
   - `forgeflow check --stage 2`가 실행되어 `GATE1_REVIEW.md`의 존재 및 `APPROVED` 상태를 검증한다.
   - 미통과 시 에이전트 도구는 `exit 1`과 함께 물리적으로 정지하며, 코드를 단 한 줄도 작성하지 않는다.
2. **이중 루프 제어 규범 (Dual-Loop Governance)**:
   - **Inner Loop (Loop 2: 수정-테스트 원자적 루프)**:
     - 에이전트는 `tasks.md`를 순차 실행하며 TDD 단위 테스트를 작성하고 코드를 구현한다.
     - 테스트 실패, 린트 오류, 사소한 컴파일 실패 발생 시 **가짜 멈춤(False Stop)을 엄격히 금지**한다.
     - 에이전트는 사용자 보고 없이 즉시 `원인 분석 → 코드 수정 → 테스트 성공 → git commit`의 1회 원자적 루프를 자율 주행한다.
     - 동일 오류로 5회 연속 무진전(Loop Budget 초과)인 경우에만 작업을 중단하고 사용자에게 에스컬레이션한다.
   - **Outer Loop (Loop 3: 아키텍처/스펙 회귀 프로토콜)**:
     - 구현 중 인터페이스 모순이나 요구사항 결함이 발견된 경우, 에이전트가 임의로 `spec.md`를 하향 축소(Spec Downgrade)하는 행위를 금지한다.
     - 에이전트는 "스펙 회귀(Loop 3 Regression)"를 공식 선언하고 기획 단계로 돌아가 `spec.md`를 수정한 후, Gate 1 재승인을 받아야만 구현을 재개할 수 있다.

### 3.5 Gate 2: QA 품질 승인 (QA Sign-off)
1. **품질 검증 통과 요건**:
   - 모든 태스크 완료 후 QA 심사를 수행한다.
   - `forgeflow review --strict`: 함수 복잡도, 중첩, 린트 Warning 0건을 확인한다.
   - 단위 및 통합 테스트 100% Pass (Fail=0, Error=0).
2. **QA 승인 증적 발행**:
   - 검증된 최종 커밋 SHA를 바인딩하여 `QA_SIGNOFF.md`를 발행하고 `Gate 2 Verdict: APPROVED`를 기록한다.
   - `PACKAGE_REVIEW_PENDING` 상태로 전이되어 최종 릴리즈 승격 준비가 완료된다.

### 3.6 Gate 3: 릴리즈 승인 및 패키지 밀봉 (Release & Seal)
1. **릴리즈 최종 승인**:
   - `QA_SIGNOFF.md`의 유효성을 최종 확인하고 `RELEASE_SIGNOFF.md` 및 `COMPLETION_REPORT.md`를 생성한다.
   - 사용자 Go/No-Go 구두 승인을 확인하여 메인 브랜치 머지를 확정한다.
2. **패키지 밀봉(Package Seal) 및 정리**:
   - `tasks/in-progress/<release-id>/` 디렉터리를 `tasks/completed/<release-id>/`로 원자적 이동한다.
   - 밀봉된 과거 릴리즈는 불변 감사 기록으로 격리되며, 향후 에이전트의 실행 지침으로 인용되지 않는다.
   - 작업 브랜치 삭제 및 Fast-Path 종료를 수행한다.

---

## 제4장. 대규모 과업(Epic) 전용 Spec of Specs 설계

### 4.1 에픽 판정 지표 (Triage Criteria)
Stage 1의 `specify` 단계에서 다음 4대 지표 중 2개 이상 해당하거나 Tier 3로 분류되는 경우, 에이전트는 단일 명세서 작성을 중단하고 **Spec of Specs (에픽 모드)**로 자동 승격을 제안한다.

1. **태스크 수**: 예상되는 원자적 태스크가 20개 이상인 경우.
2. **도메인 경계**: 2개 이상의 독립된 도메인(예: DB 모델, 코어 로직, 외부 API 등)에 영향을 미치는 경우.
3. **의존성 체인**: 선행 컴포넌트가 완성 및 검증되어야만 후속 컴포넌트의 테스트가 가능한 경우.
4. **거버넌스 티어**: 보안, 데이터 영속성, 코어 인터페이스 변경을 수반하는 Tier 3 과업인 경우.

### 4.2 에픽 디렉터리 구조 및 파트 격리 모델
에픽 단위 과업은 단일 `tasks/in-progress/` 패키지 내부에 독립된 서브 파트(`parts/`) 디렉터리를 형성하여 에이전트의 컨텍스트 피로도를 차단한다.

```text
tasks/in-progress/v1.0.0-auth-platform/         # Epic 릴리즈 패키지
├── EPIC_SPEC.md                              # [ForgeFlow] 마스터 에픽 명세 및 파트 분할 로드맵
├── GATE1_REVIEW.md                           # [ForgeFlow] 에픽 전체 아키텍처 명세 승인 증적
│
├── parts/                                    # [Spec Kit] 독립 실행 서브 파트 보관소
│   ├── 01-user-schema/                       # Part 1 (독립 세션으로 실행)
│   │   ├── spec.md / plan.md / tasks.md
│   │   └── PART_QA.md                        # Part 1 증분 검증 통과 증적
│   ├── 02-jwt-engine/                        # Part 2 (독립 세션으로 실행)
│   │   ├── spec.md / plan.md / tasks.md
│   │   └── PART_QA.md
│   └── 03-oauth-routes/                      # Part 3 (독립 세션으로 실행)
│       ├── spec.md / plan.md / tasks.md
│       └── PART_QA.md
│
├── QA_SIGNOFF.md                             # [ForgeFlow] 전체 통합 QA 최종 승인 (Gate 2)
├── RELEASE_SIGNOFF.md                        # [ForgeFlow] 최종 릴리즈 승인 (Gate 3)
└── COMPLETION_REPORT.md                      # [ForgeFlow] 에픽 완료 보고서
```

### 4.3 에픽 실행 프로토콜
1. **마스터 심사**: `EPIC_SPEC.md`에 대해 Gate 1(Tier 3 패널 심사)을 통과하여 전체 시스템 분할을 공인받는다.
2. **파트별 클린 컨텍스트 주행**:
   - 에이전트는 한 번에 하나의 파트(`parts/01-user-schema/`)만 열어 Spec Kit 워크플로우를 완주한다.
   - 해당 파트의 단위 테스트를 통과하면 `PART_QA.md`를 기록하고 세션을 종료한다.
   - 다음 파트로 진입할 때 이전 파트의 구현 로그를 버리고 인터페이스 명세만 참조하여 컨텍스트 윈도우 폭발을 원천 차단한다.
3. **종합 통합 QA (Gate 2)**:
   - 모든 파트의 `PART_QA.md`가 완결되면, 시스템 전체 통합 회귀 테스트(`full integration suite`)를 일괄 실행한다.
   - 단일 패키지로서 `QA_SIGNOFF.md`를 승인받고 패키지 밀봉으로 전이한다.

---

## 제5장. 예외 처리 및 하네스 방어 프로토콜

### 5.1 진짜 멈춤(True Stop) vs 가짜 멈춤(False Stop) 판정 기준

| 구분 | 발생 상황 | 에이전트 조치 규범 |
| :--- | :--- | :--- |
| **가짜 멈춤 (False Stop)**<br>*보고 및 종료 엄격 금지* | - 단위 테스트 실패 (`AssertionError` 등)<br>- 린트 오류 및 타입 체크 에러<br>- `review --strict` 복잡도 Warning<br>- 서브에이전트 실행 완료 | 즉시 내부 자가 치유 루프(Loop 2)로 재진입하여 코드를 수정하고 재검증한다. 사용자에게 턴을 넘기지 않는다. |
| **진짜 멈춤 (True Stop)**<br>*작업 중지 및 사용자 대기* | - 동일한 에러 핑거프린트로 5회 연속 수정 실패<br>- 스펙 모순 및 아키텍처 결함 발견 (Loop 3 회귀)<br>- 외부 권한 요구 (비밀번호, 외부 API 토큰)<br>- Gate 2 통과 후 Gate 3 사용자 릴리즈 대기 | 작업을 즉시 멈추고 현 상태, 실패 원인, 변경 diff를 보고한 뒤 사용자의 입력을 대기한다. |

### 5.2 상태 불일치(Desync) 및 Stale Lock 자동 복구
1. **Stale Lock 해제 규약**:
   - `.forgeflow/lifecycle/.*.lock` 파일이 존재할 경우, 프로세스 PID 유효성을 확인한다.
   - 해당 PID가 존재하지 않거나 비정상 종료된 경우, 락을 강제 회수하고 감사 로그에 복구 이벤트를 기록한다.
2. **라이프사이클 동기화 (`forgeflow sync`)**:
   - `tasks/in-progress/`의 물리적 아티팩트(`GATE1_REVIEW.md` 등)와 내부 상태 저장소(`LifecycleStore`) 간의 불일치가 감지되면, 파일 시스템의 승인 증적을 최우선 정본으로 삼아 상태 기계를 자동 복구한다.

### 5.3 과거 산출물 격리 (Historical Isolation)
- `tasks/completed/` 및 과거 아카이브 디렉터리는 오직 '불변 감사 장부'로만 취급한다.
- 에이전트는 현재 작업 중인 코드의 규칙이나 경로를 판단하기 위해 과거 산출물을 인용하거나 검색 컨텍스트에 포함해서는 안 된다.

---

## 제6장. 핵심 거버넌스 데이터 스키마

### 6.1 `GATE1_REVIEW.md` 스키마
```markdown
# Gate 1 Review Sign-Off: <release-id>

## 1. Governance Classification
- Release ID: <release-id>
- Risk Tier: Tier 1 | Tier 2 | Tier 3
- Review Date: YYYY-MM-DD HH:MM:SS

## 2. Pre-Implementation Review Checklist
- [x] Constitution boundaries respected
- [x] Clear Acceptance Criteria without ambiguity
- [x] Test strategy defined in plan.md

## 3. Verdict
- Status: APPROVED
- Approver: Panel (Security, Reliability, Maintainability) | Senior Reviewer
- Proceed to Stage 3 Branch: feat/<release-id>
```

### 6.2 `QA_SIGNOFF.md` 스키마
```markdown
# Gate 2 QA Sign-Off: <release-id>

## 1. Candidate Metadata
- Release ID: <release-id>
- Candidate Commit SHA: <40-char-git-sha>
- Sign-Off Date: YYYY-MM-DD HH:MM:SS

## 2. Quality & Verification Evidence
- Unit / Focused Tests: <count> passed, 0 failed
- Strict Review: 0 Warnings (forgeflow review --strict)
- Golden Fixture Matrix: QE-01 through QE-20 PASSED
- Sandbox Audit: Verified non-destructive isolated execution

## 3. Gate 2 Verdict
- Verdict: PASS
- Lifecycle State: PACKAGE_REVIEW_PENDING
```

---

## 제7장. 결론 및 향후 계획

본 상세설계서는 Spec Kit의 간결하고 유연한 대화형 작업 경험을 해치지 않으면서도, ForgeFlow가 요구하는 엄격한 엔지니어링 거버넌스를 100% 충족하는 하이브리드 아키텍처를 정의한다. 

차후 구현 마일스톤:
1. `~/.agents/skills/forgeflow/` 패키지 내 경량 오케스트레이션 지침(`SKILL.md`) 작성.
2. `.specify/extensions.yml` 및 `constitution.md` 기본 템플릿 번들링.
3. Spec Kit의 슬래시 커맨드와 ForgeFlow 상태 기계 연동 검증.
