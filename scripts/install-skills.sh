#!/usr/bin/env bash
set -euo pipefail

SKILLS_ROOT="${HOME}/.agents/skills"
mkdir -p "${SKILLS_ROOT}"

# 0. Spec Kit 핵심 스킬 자동 설치 (미설치 시)
SPECKIT_SKILLS=("speckit-specify" "speckit-clarify" "speckit-plan" "speckit-tasks" "speckit-implement" "speckit-constitution" "speckit-analyze")
MISSING_SPECKIT=false

for skill in "${SPECKIT_SKILLS[@]}"; do
  if [ ! -d "${SKILLS_ROOT}/${skill}" ]; then
    MISSING_SPECKIT=true
    break
  fi
done

if [ "$MISSING_SPECKIT" = true ]; then
  if command -v npx >/dev/null 2>&1; then
    echo "Installing missing Spec Kit agent skills via npx skills..."
    npx -y skills add -g dceoy/speckit-agent-skills \
      -s speckit-specify \
      -s speckit-clarify \
      -s speckit-plan \
      -s speckit-tasks \
      -s speckit-implement \
      -s speckit-constitution \
      -s speckit-analyze \
      -y 2>/dev/null || echo "[WARN] Automatic Spec Kit skills installation via npx failed. Proceeding..."
  else
    echo "[WARN] 'npx' not found. Spec Kit agent skills should be installed manually when Node.js is available."
  fi
else
  echo "[SKIP] Spec Kit agent skills already installed in ${SKILLS_ROOT}/."
fi

# 1. setup-forgeflow 스킬 설치
SETUP_DIR="${SKILLS_ROOT}/setup-forgeflow"
mkdir -p "${SETUP_DIR}"

cat << 'EOF' > "${SETUP_DIR}/SKILL.md"
---
name: setup-forgeflow
description: Sets up ForgeFlow governance, 2-tier knowledge system, and GitHub Spec Kit hybrid environment in the current repository.
---

# setup-forgeflow

이 스킬은 현재 작업 중인 리포지토리에 ForgeFlow 엔터프라이즈 거버넌스, 2계층 지식 관리 체계, GitHub Spec Kit 환경을 초기 구성합니다.

## 핵심 원칙: 과거 레거시 흔적 강제 폐기 (Date-Based Amnesia Policy)

- **기준일**: **2026-10-20** (ForgeFlow v0.1.0 공식 첫 릴리즈일).
- **레거시 폐기**: 2026-10-20 이전에 생성된 기존 `.forgeflow.json`, 과거 프로젝트 메모리, 이전 버전의 산출물(구버전 spec/PRD/DESIGN/tasks)은 모두 폐기 대상 레거시로 간주합니다.
- **하위 호환성 배제**: 옛버전을 보존하거나 마이그레이션하려 하지 않고, 완전히 잊은 상태(Clean Break)에서 공식 v0.1.0 규격으로 새롭게 시작합니다.
- **새 요구사항 작성**: 사용자 요구사항에 따라 `spec.md`를 v0.1.0 단일 기준으로 완전히 새롭게 작성합니다.

## 실행 절차

1. 필수 도구 및 Spec Kit 스킬 자동 점검/설치:
   - 시스템에 `forgeflow` CLI가 설치되어 있는지 확인합니다 (`command -v forgeflow`).
   - `~/.agents/skills/`에 `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-implement` 스킬이 설치되어 있는지 확인합니다.
   - 누락된 Spec Kit 스킬이 있을 경우 에이전트가 자동 설치를 진행합니다.

2. 레거시 정리 및 v0.1.0 거버넌스 설정 생성:
   - 2026-10-20 이전의 구버전 `.forgeflow.json`이 존재하거나 이전 형식이면 새 v0.1.0 설정으로 교체합니다:
   ```json
   {
     "forgeflow_version": "0.1.0",
     "governance": {
       "tasks_dir": "tasks",
       "strict_mode": true,
       "max_loop_budget": 5
     },
     "paths": {
       "in_progress": "tasks/in-progress",
       "completed": "tasks/completed"
     }
   }
   ```

3. 2계층 지식 관리 체계(2-Tier Knowledge System) 구축:
   - **Tier 1 (Fast Recognition)**: `docs/spec/ANTI_PATTERNS.md` 생성 (토큰 500자 이하의 핵심 Never-Do / Always-Do 수칙).
   - **Tier 2 (Deep Dive)**: `docs/adr/template.md`, `docs/adr/001-eliminate-git-sha-and-commit-range-bindings.md`, `docs/adr/002-remove-spec-body-hash-binding.md` 생성.
   - 과거에 논의했던 아키텍처 결정(Git SHA 결합 금지 등)을 에이전트가 망각하고 동일 실수를 반복하는 현상을 원천 방지합니다.

4. Spec Kit 로컬 실행 스크립트 및 템플릿 완비:
   - `.specify/scripts/bash/check-prerequisites.sh` (실행 권한 0o755 부여 필수)
   - `.specify/scripts/bash/setup-plan.sh`, `setup-tasks.sh`, `common.sh`, `resolve-template.sh`, `create-new-feature.sh`
   - `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`
   - CLI를 통해 원스톱으로 구성할 경우 `forgeflow init --speckit`을 호출합니다.

5. Spec Kit 헌법 및 강제 훅 주입:
   - `.specify/memory/constitution.md` 파일을 생성하여 6대 불변 거버넌스 헌법을 선언합니다:
     - 제1조 (무승인 구현 금지 - No Code Before Gate 1): `tasks/in-progress/<id>/GATE1_REVIEW.md` 승인 전 소스 코드 작성/수정 절대 금지.
     - 제2조 (가짜 멈춤 금지 - No False Stopping): 단순 테스트 실패, 린트 오류 시 사용자에게 턴을 넘기지 않고 내부 자가 치유 루프(Loop 2) 자율 완주.
     - 제3조 (원자적 루프 정의 - Atomic Remediation Unit): 1회 루프는 `원인 식별 -> 1개 수정 -> 테스트 재실행`으로 완결하며, 구현 완료 시 최종 원자적 커밋 1개를 생성.
     - 제4조 (루프 예산 및 진짜 멈춤 - Loop Budget & True Stop): 동일 오류 5회 연속 무진전 시에만 작업 중단 및 사용자 에스컬레이션.
     - 제5조 (스펙 무단 하향 금지 - No Spec Downgrade): 구현 난항을 이유로 `spec.md` 무단 축소 금지, 필요 시 Gate 1 재승인(Loop 3) 수행.
     - 제6조 (설계 안티패턴 및 ADR 필수 준수 - Anti-Patterns & Architecture Decisions): 새 기능 기획 및 명세 작성 착수 시(`speckit.specify` 단계) `docs/spec/ANTI_PATTERNS.md` 필독 및 `docs/adr/` 참조.
   - `.specify/extensions.yml` 파일을 생성하여 `before_implement` 훅을 등록합니다:
     ```yaml
     version: "1.0"
     hooks:
       before_implement:
         - extension: forgeflow-gatekeeper
           command: forgeflow check --stage 2 --quiet
           optional: false
           prompt: "ForgeFlow Gate 1 승인 증적(GATE1_REVIEW.md)의 유효성을 검증한다. 미승인 시 즉시 중단한다."
     ```
   - `.specify/templates/commands/implement.md`에 사전 게이트 검증 체크리스트를 주입합니다.

6. 릴리즈 수명주기 디렉터리 스캐폴딩:
   - `tasks/in-progress/` 및 `tasks/completed/` 디렉터리를 생성합니다.
   - `tasks/README.md`에 비-행동지침 경계 선언을 작성합니다.

7. 세션 진입점 앵커(AGENTS.md / CLAUDE.md) 비파괴적 주입:
   - 리포지토리 루트의 `AGENTS.md` (또는 `CLAUDE.md`)에 `<!-- forgeflow:boot-anchor:start -->` 주석 마커 블록으로 부팅 시퀀스를 주입하여 AI 에이전트가 작업 전 헌법, 3대 메커니즘, 공식 사양서를 자동 인지하도록 합니다. 기존 사용자 내용은 100% 보존됩니다.

8. 완료 보고:
   - 셋업 완료 상태를 요약하고, 다음 시작 명령어(`/forgeflow` 또는 `/speckit.specify "기능 설명"`)를 안내합니다.
EOF

# 2. update-forgeflow 스킬 설치
UPDATE_DIR="${SKILLS_ROOT}/update-forgeflow"
mkdir -p "${UPDATE_DIR}"

cat << 'EOF' > "${UPDATE_DIR}/SKILL.md"
---
name: update-forgeflow
description: Updates ForgeFlow globally and migrates governance configurations, constitution, hooks, and knowledge templates in an existing repository.
---

# update-forgeflow

ForgeFlow 전역 런타임 최신화와 현재 리포지토리의 거버넌스 사양 마이그레이션을 원스톱으로 수행하는 스마트 파사드(Smart Facade) 스킬입니다.

## 실행 절차

### 1단계: 전역 런타임 및 스킬 자동 최신화 (Global Upgrade Check)
1. 원격 최신 릴리즈 점검:
   - `forgeflow upgrade --check --json` 명령을 실행하여 현재 로컬 전역 설치 버전과 원격 공식 버전을 비교합니다.
2. 조건부 전역 업그레이드:
   - 원격에 새 버전이 존재할 경우(`"upgrade_available": true`), 즉시 `forgeflow upgrade`를 호출하여 OS 사용자 계정 전역 런타임(`~/.local/forgeflow`), CLI 바이너리(`~/.local/bin/forgeflow`), 및 `~/.agents/skills/`를 최신 버전으로 자동 판올림합니다.
   - 이미 전역이 최신 버전인 경우(`"upgrade_available": false`), 불필요한 재설치를 건너뛰고 즉시 2단계로 직행합니다.

### 2단계: 현재 작업 리포지토리 사양 동기화 (Local Repo Governance Migration)
1. 리포지토리 거버넌스 사양 갱신:
   - `forgeflow update` 명령을 실행합니다 (`forgeflow update --json`).
   - 이 명령은 `tasks/in-progress/` 및 `tasks/completed/` 내부의 모든 작업 산출물을 100% 보존하면서 다음을 최신 표준으로 동기화합니다:
     - `.forgeflow.json` 설정 버전
     - `.specify/scripts/bash/` (0o755 실행 권한 포함)
     - `.specify/templates/` 및 헌법(`.specify/memory/constitution.md`)
     - 2계층 지식 관리 체계: `docs/spec/ANTI_PATTERNS.md` 및 `docs/adr/` 최신화
     - `AGENTS.md` 세션 진입점 앵커 블록
2. 거버넌스 무결성 검증:
   - `forgeflow check --quiet` 명령을 실행하여 마이그레이션 후 거버넌스 무결성을 검증합니다.
3. 결과 보고:
   - 전역 런타임 업그레이드 여부, 로컬 리포지토리 사양 갱신 내역 및 버전 정보, 정합성 검증 결과를 사용자에게 명확히 보고합니다.
EOF

# 3. forgeflow 스킬 설치 (Master Workflow Orchestrator)
FORGEFLOW_DIR="${SKILLS_ROOT}/forgeflow"
mkdir -p "${FORGEFLOW_DIR}"

cat << 'EOF' > "${FORGEFLOW_DIR}/SKILL.md"
---
name: forgeflow
description: ForgeFlow 자율 거버넌스 마스터 오케스트레이터. 새로운 기능 개발, 버그 수정, 리팩토링 시 기획부터 릴리즈 밀봉까지 전 과정을 안내하고 통제합니다. (트리거: /forgeflow, forgeflow 시작, 개발 시작, 기능 추가, 작업 시작)
---

# forgeflow

ForgeFlow 자율 거버넌스 워크플로우의 마스터 오케스트레이터입니다.
새로운 기능 개발, 결함 수정, 아키텍처 리팩토링 요청이 들어왔을 때 5단계 폐루프 수명주기를 표준화된 방식으로 시작하고 완결하도록 지원합니다.

## When to use

- 사용자가 `/forgeflow` 또는 "개발 시작", "기능 구현", "버그 수정", "거버넌스 진행" 등을 요청했을 때
- 새로운 릴리즈/과업을 시작하며 기획부터 배포까지 정석 절차를 밟고자 할 때

## 5단계 수명주기 실행 가이드

### Stage 1: 기획 & 명세 (Planning & Specification)
1. **사전 지식 인지 (기획 착수 시 필수 확인)**:
   - 기능 기획 및 명세서(`spec.md`) 작성 전, 반드시 `docs/spec/ANTI_PATTERNS.md`를 필독하여 설계 금기 사항(Git SHA 결합, spec body hash 등)을 확인합니다.
   - 대규모/구조적 변경인 경우 `docs/adr/`을 확인하고 필요 시 새 ADR 초안을 작성합니다.
   - 코드베이스 구조 및 의존성 파악이 필요하면 무차별 파일 읽기 대신 `/forgeflow-graphify`를 먼저 활용합니다. (단, `graphify` CLI 사전 설치 필수)
2. **명세 작성**:
   - `/speckit.specify "<기능 요구사항 요약>"` 실행하여 `tasks/in-progress/<release-id>/spec.md` 생성.
   - 불명확하거나 누락된 요구사항이 있다면 `/speckit.clarify`를 통해 최대 5개 질문으로 정밀 명세화.

### Gate 1: 명세 승인 (Gate 1 Review)
1. **위험도 판정 (Dynamic Tiering)**:
   - Tier 1: 단순 문구/단일 모듈 무인터페이스 버그픽스 (Self-Review PASS).
   - Tier 2: 일반 기능 및 복수 모듈 개선 (독립 시니어 1인 승인).
   - Tier 3: 코어/보안/아키텍처/의존성/거버넌스 변경 (3인 독립 패널 심사 및 승인).
2. **승인 문서 작성**:
   - `tasks/in-progress/<release-id>/GATE1_REVIEW.md`에 판정 및 "APPROVED" 기록.
   - **No Code Before Gate 1 Pass**: GATE1_REVIEW.md 승인 전에는 소스 코드 작성이 절대 금지됩니다.

### Stage 2: 기술 설계 & 태스크 분해 (Design & Tasks)
1. `/speckit.plan`을 실행하여 `plan.md` 생성 (아키텍처, 데이터 모델, 보안/영향도 분석).
2. `/speckit.tasks`를 실행하여 `tasks.md` 생성 (의존성 순서의 원자적 TDD 체크리스트).
3. 사전 검증 훅 통과 확인: `forgeflow check --stage 2` 실행하여 통과 확인.

### Stage 3: 격리 구현 & 자가 치유 루프 (Isolated Implementation & Self-Healing)
1. **작업 브랜치 분기**: `git checkout -b feat/<release-id>`
2. **순차 TDD 구현**: `tasks.md` 체크리스트 순서대로 테스트 작성 -> 구현 코드 작성.
3. **Loop 2 자율 치유 (No False Stopping)**:
   - 테스트 실패 시 턴을 멈추지 않고 스스로 원인 분석 -> 수정 -> 재테스트 5회 자율 완주.
   - 각 태스크 완료 시 원자적 체크포인트 커밋 생성.

### Gate 2 & 3: QA 품질 승인 및 릴리즈 밀봉 (Sign-Off & Package Seal)
1. **검증 통제**:
   - 전체 단위/통합 테스트 100% 통과 확인.
   - `forgeflow check --all --strict` 실행하여 거버넌스 감사 통과.
2. **Gate 2 QA 승인**:
   - `QA_SIGNOFF.md` 작성 및 Gate 2 APPROVED 서명.
3. **Gate 3 릴리즈 승인 및 밀봉**:
   - `forgeflow lifecycle seal <release-id> <candidate-sha>` 실행하여 패키지 무결성 밀봉.
   - `RELEASE_SIGNOFF.md` 작성 및 사용자 Go 판정 기록.
   - `forgeflow lifecycle complete <release-id>` 실행하여 패키지를 `tasks/completed/`로 이동.
   - 작업 브랜치 병합 및 정리.
EOF

# 4. forgeflow-graphify 스킬 설치 (Code AST & Dependency Knowledge Explorer)
GRAPHIFY_DIR="${SKILLS_ROOT}/forgeflow-graphify"
mkdir -p "${GRAPHIFY_DIR}"

cat << 'EOF' > "${GRAPHIFY_DIR}/SKILL.md"
---
name: forgeflow-graphify
description: 코드베이스의 AST 및 모듈 간 호출·의존 관계 지식 그래프를 생성·조회하여, 대량 소스 코드 무차별 읽기(grep/read_file)를 방지하고 최소 컨텍스트 토큰으로 아키텍처 및 의존성을 초고속 탐색합니다. (트리거: /forgeflow-graphify, forgeflow:graphify, 코드 구조 파악, 의존성 지도, 호출 관계 추적, 아키텍처 탐색)
---

# forgeflow-graphify

코드베이스와 문서의 AST 및 모듈 간 호출 관계 지도를 조회하여, 토큰 낭비 없는 초고속 구조 탐색을 제공합니다.

> [!IMPORTANT]
> **외부 도구 전제조건 (External Tool Prerequisite)**:
> 본 스킬은 시스템에 **`graphify` CLI** 도구가 사전 설치되어 있어야 동작합니다.

## When to use

- 사용자가 `/forgeflow-graphify` 또는 "코드 구조 파악", "의존성 지도", "호출 관계 추적", "아키텍처 탐색"을 요청할 때
- 기능 기획/명세 착수 전, 어떤 파일들과 심볼들이 상호 연결되어 있는지 파악해야 할 때
- 수십 개 파일의 코드를 무차별적으로 `read_file`하거나 과도한 `grep`으로 컨텍스트 윈도우를 소진하지 않으려 할 때

## Instructions

에이전트는 코드베이스 구조를 파악하거나 호출 관계를 추적할 때 다음 절차를 준수하여 `graphify` CLI를 활용하십시오.

### 1단계: graphify CLI 설치 확인
에이전트는 먼저 시스템에 `graphify` 도구가 설치되어 있는지 확인합니다:
```bash
command -v graphify
```
- **미설치 시**:
  - `graphify`가 설치되어 있지 않으면 작업을 진행할 수 없습니다.
  - 에이전트는 즉시 사용자에게 `graphify` 도구의 설치를 안내하고 확인을 요청합니다:
    > "이 스킬을 사용하려면 `graphify` CLI 도구가 필요해요. `pip install graphify` 등을 통해 도구를 먼저 설치해 주세요."

### 2단계: 색인 상태 확인 및 빌드 (Index Build & Update)
대상 디렉터리(또는 프로젝트 루트)에 `graphify-out/graph.json`이 존재하는지 확인합니다:
- **색인이 없거나 초기 빌드가 필요한 경우**:
  ```bash
  graphify extract <target_path> --code-only
  ```
  (로컬 Tree-sitter AST 기반으로 파싱하며 LLM API 호출 없이 즉시 생성됩니다)
- **코드가 일부 수정되어 증분 갱신이 필요한 경우**:
  ```bash
  graphify update <target_path>
  ```

### 3단계: 주요 탐색 명령어 (Token-Saving Exploration)
필요한 정보의 성격에 맞춰 적절한 명령어를 실행합니다:
1. **특정 심볼/모듈의 의존성 및 연결 관계 조회**:
   ```bash
   graphify explain "<Node_or_File_Name>" [--graph <path/to/graph.json>]
   ```
   - 특정 함수, 클래스, 파일이 import하거나 포함하는 심볼 및 역방향 참조를 즉시 반환합니다.
2. **두 심볼 간의 최단 호출/의존 경로 탐색**:
   ```bash
   graphify path "<Source_Node>" "<Target_Node>" [--graph <path/to/graph.json>]
   ```
   - 모듈 간 또는 함수 간 어떤 호출 체인을 거쳐 연결되는지 최소 홉(hop) 단위로 출력합니다.
3. **시각화 HTML 내보내기**:
   ```bash
   graphify export html [--graph <path/to/graph.json>]
   ```
   - 브라우저에서 직접 인터랙티브하게 탐색할 수 있는 독립형 `graph.html`을 생성합니다.

### 4단계: 핵심 연결 파일 선별 및 최소 읽기 (Selective Reading)
- 수십 개 파일 전체를 순차적으로 읽지 않습니다.
- `graphify explain` / `graphify path`로 작업 대상과 직접 연결된 핵심 파일 및 함수 목록을 1차 필터링합니다.
- 필터링된 최소한의 파일에 대해서만 특정 라인 범위를 지정하여 `read_file`을 실행함으로써 컨텍스트 토큰을 최대 80% 이상 절감합니다.
EOF

chmod +x "${SETUP_DIR}/SKILL.md" "${UPDATE_DIR}/SKILL.md" "${FORGEFLOW_DIR}/SKILL.md" "${GRAPHIFY_DIR}/SKILL.md" 2>/dev/null || true
echo "[PASS] ForgeFlow 스킬 제품군 (/forgeflow, /forgeflow-graphify, /setup-forgeflow, /update-forgeflow)이 ${SKILLS_ROOT}/ 에 성공적으로 설치되었습니다."
