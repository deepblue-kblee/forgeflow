# 🌊 ForgeFlow (포지플로우) v0.1.16

**GitHub Spec Kit 결합형 자율 AI 에이전트 거버넌스 프레임워크 & 게이트키퍼 CLI**  
*(Autonomous Agent Governance Framework & Gatekeeper CLI for GitHub Spec Kit)*

---

## 🌟 개요 (Overview)

ForgeFlow는 **GitHub Spec Kit**의 대화형 명세 기반 개발(Spec-Driven Development) 실행력과 **ForgeFlow**의 엔터프라이즈 하네스 거버넌스(Harness Governance) 통제력을 유기적으로 결합한 차세대 자율 AI 에이전트 개발 파이프라인입니다.

### 이중 엔진 및 2계층 지식 관리 아키텍처 (Architecture)
1. **실행 엔진 (Worker) — GitHub Spec Kit**:
   - 대화형 인터뷰를 통한 요구사항 발굴 및 명세서(`spec.md`) 작성
   - 기술 계획(`plan.md`) 및 원자적 태스크 분해(`tasks.md`)
   - TDD 기반 순차 구현 주도
2. **거버넌스 엔진 (Supervisor) — ForgeFlow**:
   - 릴리즈 수명주기 관리 (`tasks/in-progress/` ──► `tasks/completed/`)
   - Gate 1 명세 승인(`GATE1_REVIEW.md`) 및 fail-closed 사전 차단 (`forgeflow check --stage 2`)
   - Gate 2 QA Sign-Off (`QA_SIGNOFF.md`)
   - Gate 3 릴리즈 승인 및 패키지 무결성 밀봉 (Package Manifest SHA256)
3. **2계층 지식 관리 체계 (2-Tier Knowledge Architecture)**:
   - **Tier 1 (Fast Recognition)**: `docs/spec/ANTI_PATTERNS.md` (500토큰 미만 핵심 Never-Do / Always-Do 수칙). 세션 부팅 시의 상시 토큰 낭비를 배제하고, 새 기능 기획 및 명세 작성 시작 시점(`/speckit.specify`)에 집중 확인하여 설계 실수 재발을 원천 방지합니다.
   - **Tier 2 (Deep Dive)**: `docs/adr/` (아키텍처 결정 레코드). Git SHA 결합 제거(ADR 001), spec body hash 바인딩 제거(ADR 002) 등 주요 기술적 의사결정의 배경과 근거를 영구 보존하여 심층 맥락 필요 시 온디맨드로 참조합니다.

### 핵심 설계 원칙:
- **Zero-Dependency 원칙**: 외부 서드파티 런타임 의존성 없이 Python 3.10+ 표준 라이브러리만으로 100% 동작합니다.
- **Fail-Closed Gatekeeper 원칙**: Gate 1 승인 증적이 누락된 경우 코드를 단 한 줄도 작성하지 못하도록 물리적으로 차단합니다.
- **실용적 안전 불변식 원칙 (De-SHA per ADR 001)**: 취약한 Git commit diff range 및 SHA 바인딩을 제거하고 실용적인 안전 불변식(테스트 100% 통과 + Gate 승인 증적 + clean worktree + 패키지 매니페스트 SHA256)으로 신뢰성을 보장합니다.
- **Progressive Disclosure 원칙**: 타겟 프로젝트에 무거운 프레임워크 문서를 주입하지 않고, 오직 `.forgeflow.json`, `.specify/`, `docs/adr/`, `tasks/`만 최소한으로 유지합니다.
- **Atomic Remediation Loop 원칙**: 단순 단위 테스트 실패는 중단 사유가 아니며, `원인 식별 ➔ 코드 수정 ➔ 테스트 성공` 단위를 에이전트가 최대 5회 자율 완주하고, 구현 완료 시 원자적 커밋 1개를 생성합니다.

---

## 🚀 빠른 시작 (Quick Start)

사용자는 ForgeFlow 저장소를 클론(clone)할 필요 없이 사용자 계정 로컬 환경에 원클릭으로 설치하고, 스킬과 함께 동일한 생명주기로 관리할 수 있습니다.

### 1. 사용자 로컬 설치 (Zero-Clone Installation)

#### 방법 A. AI 에이전트를 통한 대행 설치 (가장 추천)
임의의 AI 에이전트(Claude Code, Antigravity, OpenClaw 등) 대화창에 아래 프롬프트를 입력하세요:

```text
https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh 스크립트를 다운로드하여 실행해 주세요. 
사용자 계정의 ~/.local/bin 경로에 forgeflow CLI와 ~/.agents/skills/ 에 forgeflow, forgeflow-graphify, setup-forgeflow, update-forgeflow 스킬이 
설치되었는지 확인해 주세요.
```

#### 방법 B. 개발자 직접 설치 (터미널)
터미널에서 원클릭 명령어로 CLI와 에이전트 스킬을 계정 로컬에 동시에 설치합니다:
```bash
curl -sSL https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh | bash
```

설치 완료 시:
- CLI 실행 진입점: `~/.local/bin/forgeflow` (호환 별칭: `~/.local/bin/harness`)
- 사용자 에이전트 스킬:
  - `~/.agents/skills/forgeflow/` (마스터 오케스트레이터 `/forgeflow`)
  - `~/.agents/skills/forgeflow-graphify/` (코드 AST 및 의존성 탐색 `/forgeflow-graphify`)
  - `~/.agents/skills/setup-forgeflow/` (거버넌스 & 지식 체계 초기화 `/setup-forgeflow`)
  - `~/.agents/skills/update-forgeflow/` (전역 및 로컬 사양 동기화 `/update-forgeflow`)
- 버전 확인: `forgeflow --version`

---

## 🛠️ 프로젝트에 거버넌스 적용하기

### 1. 신규 프로젝트 환경 구성 (`/setup-forgeflow`)
개발 대상 저장소 루트로 이동하여 에이전트에게 지시합니다:
```text
/setup-forgeflow
```
*(CLI 직접 실행: `forgeflow init --speckit`)*

자동 생성되는 프로젝트 레이아웃:
```text
<project-root>/
├── .forgeflow.json                     # 프로젝트 거버넌스 설정
├── .specify/                           # Spec Kit 연동 환경
│   ├── memory/constitution.md          # 6대 불변 거버넌스 헌법
│   ├── extensions.yml                  # before_implement 강제 차단 훅
│   ├── templates/commands/implement.md # 사전 검증 체크리스트
│   ├── templates/                      # spec-template, plan-template, tasks-template
│   └── scripts/bash/                   # check-prerequisites.sh, setup-plan.sh, setup-tasks.sh
├── docs/                               # 2계층 지식 관리 체계
│   ├── spec/ANTI_PATTERNS.md           # Tier 1 빠른 인지 (금기 안티패턴)
│   └── adr/                            # Tier 2 심층 아키텍처 결정 레코드
└── tasks/                              # 릴리즈 패키지 보관소
    ├── in-progress/                    # 현재 진행 중인 활성 패키지
    └── completed/                      # 밀봉된 과거 릴리즈 아카이브
```

### 2. 마스터 오케스트레이터로 개발 시작 (`/forgeflow`)
새로운 기능 구현, 결함 수정, 리팩토링 착수 시 에이전트에게 명령합니다:
```text
/forgeflow "<구현할 기능 또는 버그 수정 내용>"
```
- 기획(`spec.md`) 작성 전 `docs/spec/ANTI_PATTERNS.md`를 자동 필독하여 금기 설계 패턴을 사전 배제합니다.
- 기술 설계(`plan.md`), 태스크 분해(`tasks.md`), Gate 1 승인, TDD 격리 구현, Gate 2 QA 승인, Gate 3 릴리즈 밀봉까지의 5단계 폐루프 수명주기를 표준화된 절차로 오케스트레이션합니다.

### 3. 코드베이스 초고속 구조 탐색 (`/forgeflow-graphify`)
기능 개발 전 대량의 소스 코드를 무차별로 읽지 않고, AST 및 호출·의존 관계 지도를 빠르게 조회합니다:
```text
/forgeflow-graphify
```
*(전제 조건: `graphify` CLI 사전 설치)*
- `graphify explain "<모듈명>"` 또는 `graphify path "<출발>" "<도착>"` 명령으로 연결된 핵심 파일만 선별.
- 선별된 파일만 특정 라인 단위로 정밀 조회하여 컨텍스트 윈도우 토큰을 최대 80% 이상 절감합니다.

### 4. 전역 런타임 업그레이드 (`forgeflow upgrade`)
터미널에서 언제든 OS 사용자 계정 전역의 ForgeFlow CLI 및 에이전트 스킬을 최신 버전으로 업그레이드할 수 있습니다:
```bash
# 최신 버전 확인 (설치하지 않고 확인만 수행)
forgeflow upgrade --check

# 전역 최신 버전으로 자동 업그레이드
forgeflow upgrade
```

### 5. 로컬 프로젝트 거버넌스 사양 동기화 (`forgeflow update`)
현재 작업 리포지토리의 거버넌스 사양(`.forgeflow.json`, `.specify/scripts/bash/`, 템플릿, `docs/spec/ANTI_PATTERNS.md`, `docs/adr/`)을 현재 설치된 최신 규격으로 동기화합니다:
```bash
# 현재 프로젝트 거버넌스 사양 갱신 (tasks 작업 데이터 100% 보존)
forgeflow update
```

### 6. 작업 프로젝트 스마트 업데이트 (`/update-forgeflow`)
어느 작업 리포지토리에서든 한 줄로 지시하면 전역 런타임 최신화와 현재 프로젝트 거버넌스 사양 갱신을 원스톱으로 처리합니다:
```text
/update-forgeflow
```
- **스마트 파사드(Smart Facade)**: 원격에 새 버전이 있다면 전역 런타임(`forgeflow upgrade`)을 먼저 자동 실행하고, 이어서 현재 프로젝트의 로컬 거버넌스 갱신(`forgeflow update`)을 호출합니다.
- 진행 중인 작업 내역(`tasks/in-progress/`, `tasks/completed/`)은 일절 변경 없이 안전하게 보존됩니다.

### 7. 경량 내장 이슈 트래커 (`forgeflow issue`)
외부 의존성 없이 프레임워크 자체 CLI로 GitHub Issues를 조회하고 로컬 캐시(`.cache/issues/`)와 연동합니다:
```bash
forgeflow issue list                   # 열려 있는 이슈 조회
forgeflow issue view <번호>            # 특정 이슈 상세 조회
forgeflow issue create --title "..."   # 새 이슈 등록
forgeflow issue close <번호>           # 이슈 종결
```

---

## 🌊 엔드투엔드 개발 워크플로우

Stage(작업 수행 단계)와 Gate(품질 및 명세 승인 관문)를 명확히 분리하여, 어느 시점에 어떤 승인이 이루어지는지 직관적으로 제어합니다.

### 1. 표준 흐름도 (Canonical Workflow)

```text
[Stage 1: 기획 & 명세 작성]
   - 사전 점검: docs/spec/ANTI_PATTERNS.md 확인 (필요 시 docs/adr/ 및 /forgeflow-graphify 활용)
   - 도구: /speckit.specify ➔ /speckit.clarify
   - 결과물: tasks/in-progress/<id>/spec.md
       │
       ▼
[Gate 1: 명세 승인 (Spec Sign-Off)]  <--- ★ Gate 1 승인 관문
   - 수행: 리스크 판정(Tier 1/2/3) 및 GATE1_REVIEW.md 발행
   - 승인 주체: Tier 1=AI 자체 승인 / Tier 2=독립 에이전트 검토 / Tier 3=3대 패널 심사 후 사용자 대화 승인
   - 완료 상태: GATE1_REVIEW.md 내 "Gate 1 Verdict: APPROVED"
   - 잠금 해제: Stage 2 기술 설계 및 Stage 3 구현 착수 허용 (No Code Before Gate 1 Pass)
       │
       ▼
[Stage 2: 기술 설계 & 태스크 분해]
   - 도구: /speckit.plan (plan.md) ➔ /speckit.tasks (tasks.md)
       │
       ▼
[Stage 3: 격리 구현 & 자가 치유]
   - 도구: /speckit.implement (TDD 순차 구현)
   - 사전 가드: before_implement 훅이 forgeflow check --stage 2 실행 ➔ Gate 1 APPROVED 증적 확인
   - Inner Loop (Loop 2): 테스트 실패 시 분석 ➔ 수정 ➔ 테스트 성공 ➔ 원자적 커밋 자율 주행 (동일 결함 5회 한도)
       │
       ▼
[Gate 2: QA 품질 승인 (QA Sign-Off)]  <--- ★ Gate 2 승인 관문
   - 수행: forgeflow review --strict (정적 분석) + 전체 단위/통합 테스트 100% Pass
   - 안전 불변식: ADR 001에 따라 취약한 commit diff range를 배제하고 실질적 안전성 검증
   - 생성물: QA_SIGNOFF.md 발행
   - 승인 주체: QA 심사관 에이전트 (Tier 3는 3대 독립 패널 검증)
   - 완료 상태: QA_SIGNOFF.md 내 "Gate 2 Verdict: APPROVED"
   - 잠금 해제: 최종 릴리즈 승격 준비 허용
       │
       ▼
[Gate 3: 릴리즈 승인 및 패키지 밀봉 (Release Sign-Off)]  <--- ★ Gate 3 승인 관문
   - 수행: RELEASE_SIGNOFF.md 및 COMPLETION_REPORT.md 발행
   - 승인 주체: 최종 사용자 (User Go/No-Go 구두 승인)
   - 완료 상태: RELEASE_SIGNOFF.md 내 "Gate 3 Verdict: APPROVED"
   - 패키지 밀봉: Package Manifest SHA256 검증 및 tasks/in-progress/<id> ➔ tasks/completed/<id> 이동
   - 브랜치 정리: main 병합 및 작업 브랜치 삭제 (Fast-Path Close)
```

### 2. 게이트(Gate) 요약 매트릭스

| 항목 | Gate 1 (명세 승인 / Spec Sign-Off) | Gate 2 (QA 품질 승인 / QA Sign-Off) | Gate 3 (릴리즈 승인 / Release Sign-Off) |
| :--- | :--- | :--- | :--- |
| **Before (전제 조건)** | Stage 1 완료 (`spec.md` 작성 및 모호성 해소) | Stage 3 구현 완료, 전체 테스트 통과, 작업 커밋 생성 | Gate 2 `APPROVED` 완료, 릴리즈 커밋 생성 |
| **Run (실제 CLI 명령)** | `forgeflow check --stage 2` (또는 implement 진입 시 훅 자동 검증) | `forgeflow review --strict` 및 `forgeflow lifecycle package-review <qa-sha>` | `forgeflow lifecycle seal <rc-sha>` 및 `forgeflow lifecycle complete <id>` |
| **Creates (생성 산출물)** | `tasks/in-progress/<id>/GATE1_REVIEW.md` | `tasks/in-progress/<id>/QA_SIGNOFF.md` | `RELEASE_SIGNOFF.md`, `COMPLETION_REPORT.md` |
| **User action (승인 방식)** | Tier 1: 자동 통과 / Tier 2: 결과 확인 / Tier 3: 사용자 대화창 구두 승인 ("승인합니다") | `QA_SIGNOFF.md`의 `APPROVED` 확인 | 사용자 Go/No-Go 최종 배포 구두 승인 |
| **Done when (완료 조건)** | `GATE1_REVIEW.md` 내 `Gate 1 Verdict: APPROVED` 기록 완료 | 단위/통합 테스트 0 실패, 린트 0 Warning, Gate 2 APPROVED | 릴리즈 산출물 완성 및 `tasks/completed/` 원자적 이동 완료 |
| **Unlocks (허용 작업)** | Stage 2 기술 설계 (`plan.md`, `tasks.md`) 및 작업 브랜치 생성 | Gate 3 최종 배포 승격 준비 | main 브랜치 머지 및 피쳐 브랜치 정리 (Fast-Path Close) |
