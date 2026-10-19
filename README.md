# 🌊 ForgeFlow (포지플로우) v0.1.0

**GitHub Spec Kit 결합형 자율 AI 에이전트 거버넌스 프레임워크 & 게이트키퍼 CLI**  
*(Autonomous Agent Governance Framework & Gatekeeper CLI for GitHub Spec Kit)*

---

## 🌟 개요 (Overview)

ForgeFlow는 **GitHub Spec Kit**의 대화형 명세 기반 개발(Spec-Driven Development) 실행력과 **ForgeFlow**의 엔터프라이즈 하네스 거버넌스(Harness Governance) 통제력을 유기적으로 결합한 차세대 자율 AI 에이전트 개발 파이프라인입니다.

### 이중 엔진 아키텍처 (Dual-Engine Architecture)
1. **실행 엔진 (Worker) — GitHub Spec Kit**:
   - 대화형 인터뷰를 통한 요구사항 발굴 및 명세서(`spec.md`) 작성
   - 기술 계획(`plan.md`) 및 원자적 태스크 분해(`tasks.md`)
   - TDD 기반 순차 구현 주도
2. **거버넌스 엔진 (Supervisor) — ForgeFlow**:
   - 릴리즈 수명주기 관리 (`tasks/in-progress/` ──► `tasks/completed/`)
   - Gate 1 사전 심사(`GATE1_REVIEW.md`) 및 `spec.md` SHA-256 불변 바인딩
   - 구현 시작 전 Gate 1 통과 여부를 기계적으로 차단하는 Fail-Closed 게이트키퍼 (`forgeflow check --stage 2`)
   - Gate 2 QA Sign-Off 및 커밋 SHA 바인딩 (`QA_SIGNOFF.md`)
   - Gate 3 릴리즈 승인 및 패키지 밀봉(Package Seal)

### 핵심 설계 원칙:
- **Zero-Dependency 원칙**: 외부 서드파티 런타임 의존성 없이 Python 3.10+ 표준 라이브러리만으로 100% 동작합니다.
- **Fail-Closed Gatekeeper 원칙**: Gate 1 승인 증적이 누락되었거나 `spec.md`가 변조된 경우 코드를 단 한 줄도 작성하지 못하도록 물리적으로 차단합니다.
- **Progressive Disclosure 원칙**: 타겟 프로젝트에 무거운 프레임워크 문서를 주입하지 않고, 오직 `.forgeflow.json`, `.specify/`, `tasks/`만 최소한으로 유지합니다.
- **Atomic Remediation Loop 원칙**: 단순 단위 테스트 실패는 중단 사유가 아니며, `원인 식별 ➔ 코드 수정 ➔ 테스트 성공 ➔ git commit` 단위를 에이전트가 최대 5회 자율 완주합니다.

---

## 🚀 빠른 시작 (Quick Start)

사용자는 ForgeFlow 저장소를 클론(clone)할 필요 없이 사용자 계정 로컬 환경에 원클릭으로 설치하고, 스킬과 함께 동일한 생명주기로 관리할 수 있습니다.

### 1. 사용자 로컬 설치 (Zero-Clone Installation)

#### 방법 A. AI 에이전트를 통한 대행 설치 (가장 추천)
임의의 AI 에이전트(Claude Code, Antigravity, OpenClaw 등) 대화창에 아래 프롬프트를 입력하세요:

```text
https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh 스크립트를 다운로드하여 실행해 주세요. 
사용자 계정의 ~/.local/bin 경로에 forgeflow CLI와 ~/.agents/skills/ 에 setup-forgeflow, update-forgeflow 스킬이 
설치되었는지 확인해 주세요.
```

#### 방법 B. 개발자 직접 설치 (터미널)
터미널에서 원클릭 명령어로 CLI와 에이전트 스킬을 계정 로컬에 동시에 설치합니다:
```bash
curl -sSL https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh | bash
```

설치 완료 시:
- CLI 실행 진입점: `~/.local/bin/forgeflow` (호환 별칭: `~/.local/bin/harness`)
- 사용자 에이전트 스킬: `~/.agents/skills/setup-forgeflow/`, `~/.agents/skills/update-forgeflow/`
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
│   ├── memory/constitution.md          # 5대 불변 거버넌스 헌법
│   ├── extensions.yml                  # before_implement 강제 차단 훅
│   └── templates/commands/implement.md # 사전 검증 체크리스트
└── tasks/                              # 릴리즈 패키지 보관소
    ├── in-progress/                    # 현재 진행 중인 활성 패키지
    └── completed/                      # 밀봉된 과거 릴리즈 아카이브
```

### 2. 기존 프로젝트 업데이트 및 마이그레이션 (`/update-forgeflow`)
ForgeFlow 판올림 시 기존 프로젝트에서 지시합니다:
```text
/update-forgeflow
```
- 진행 중인 작업 내역을 안전하게 보존하면서 헌법과 훅 설정을 최신 규격으로 자동 마이그레이션합니다.

---

## 🌊 엔드투엔드 개발 워크플로우

1. **Stage 1 (기획 & 명세 작성)**:
   - `/speckit.specify "새로운 기능 요구사항"`
   - `/speckit.clarify` (대화형 인터뷰를 통해 모호성 제거 및 Acceptance Criteria 확정)
2. **Stage 2 (Gate 1 사전 심사)**:
   - `forgeflow gate1 review`
   - 리스크 티어링(Tier 1/2/3) 심사, `spec.md` SHA-256 해시 바인딩 및 `GATE1_REVIEW.md` 생성
3. **Stage 3 (기술 설계 & 태스크 분해)**:
   - `/speckit.plan` (아키텍처, 데이터 모델, 에러 처리 규격)
   - `/speckit.tasks` (원자적 체크리스트 분해)
4. **Stage 4 (격리 구현, 자가 치유 및 Gate 2 QA Sign-Off)**:
   - `/speckit.implement` (진입 시 `.specify/extensions.yml`의 `forgeflow check --stage 2`가 자동 실행되어 Gate 1 미승인 시 물리적으로 코드 작성을 차단)
   - Inner Loop (Loop 2): 테스트 실패 시 `분석 ➔ 수정 ➔ 테스트 성공 ➔ git commit` 자율 주행 (동일 결함 5회 한도)
   - `forgeflow gate2 signoff`: 엄격 리뷰, 커밋 SHA 바인딩 및 `QA_SIGNOFF.md` 발행
5. **Stage 5 (Gate 3 릴리즈 승인 및 패키지 밀봉)**:
   - `forgeflow release`: `RELEASE_SIGNOFF.md` 및 `COMPLETION_REPORT.md` 생성
   - 패키지를 `tasks/completed/`로 원자적 이동하여 안전하게 밀봉
