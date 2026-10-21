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
description: Sets up ForgeFlow governance and GitHub Spec Kit hybrid environment in the current repository.
---

# setup-forgeflow

이 스킬은 현재 작업 중인 리포지토리에 ForgeFlow 엔터프라이즈 거버넌스와 GitHub Spec Kit 환경을 초기 구성합니다.

## 핵심 원칙: 과거 레거시 흔적 강제 폐기 (Date-Based Amnesia Policy)

- **기준일**: **2026-10-20** (ForgeFlow v0.1.0 공식 첫 릴리즈일).
- **레거시 폐기**: 2026-10-20 이전에 생성된 기존 `.forgeflow.json`, 과거 프로젝트 메모리, 이전 버전의 산출물(구버전 spec/PRD/DESIGN/tasks)은 모두 폐기 대상 레거시로 간주합니다.
- **하위 호환성 배제**: 옛버전을 보존하거나 마이그레이션하려 하지 않고, 완전히 잊은 상태(Clean Break)에서 공식 v0.1.0 규격으로 새롭게 시작합니다.
- **새 요구사항 작성**: 사용자 요구사항에 따라 `spec.md`를 v0.1.0 단일 기준으로 완전히 새롭게 작성합니다.

## 실행 절차

1. 필수 도구 및 Spec Kit 스킬 자동 점검/설치:
   - 시스템에 `forgeflow` CLI가 설치되어 있는지 확인합니다 (`command -v forgeflow`).
   - `~/.agents/skills/`에 `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-implement` 스킬이 설치되어 있는지 확인합니다.
   - 누락된 Spec Kit 스킬이 있을 경우 에이전트가 다음 명령을 실행하여 자동으로 설치를 완료합니다 (이미 설치되어 있으면 건너뜁니다):
     ```bash
     npx -y skills add -g dceoy/speckit-agent-skills -s speckit-specify -s speckit-clarify -s speckit-plan -s speckit-tasks -s speckit-implement -s speckit-constitution -s speckit-analyze -y
     ```

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

3. Spec Kit 로컬 실행 스크립트 및 템플릿 완비:
   - 후속 Spec Kit 스킬(`/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`)이 정상 동작할 수 있도록 프로젝트 로컬 전제조건을 구성합니다:
     - `.specify/scripts/bash/check-prerequisites.sh` (실행 권한 부여 필수)
     - `.specify/scripts/bash/setup-plan.sh`
     - `.specify/scripts/bash/setup-tasks.sh`
     - `.specify/templates/spec-template.md`
     - `.specify/templates/plan-template.md`
     - `.specify/templates/tasks-template.md`
   - CLI를 통해 원스톱으로 구성할 경우 `forgeflow init --speckit`을 호출합니다.

4. Spec Kit 헌법 및 강제 훅 주입:
   - `.specify/memory/constitution.md` 파일을 생성하여 5대 불변 거버넌스 헌법을 선언합니다:
     - 제1조 (무승인 구현 금지 - No Code Before Gate 1): `tasks/in-progress/<id>/GATE1_REVIEW.md` 승인 전 소스 코드 작성/수정 절대 금지.
     - 제2조 (가짜 멈춤 금지 - No False Stopping): 단순 테스트 실패, 린트 오류 시 사용자에게 턴을 넘기지 않고 내부 자가 치유 루프(Loop 2) 자율 완주.
     - 제3조 (원자적 루프 정의 - Atomic Remediation Unit): 1회 루프는 `원인 식별 -> 1개 수정 -> 테스트 재실행`으로 완결하며, 구현 완료 시 최종 원자적 커밋 1개를 생성.
     - 제4조 (루프 예산 및 진짜 멈춤 - Loop Budget & True Stop): 동일 오류 5회 연속 무진전 시에만 작업 중단 및 사용자 에스컬레이션.
     - 제5조 (스펙 무단 하향 금지 - No Spec Downgrade): 구현 난항을 이유로 `spec.md` 무단 축소 금지, 필요 시 Gate 1 재승인(Loop 3) 수행.
   - 헌법 하단에 공식 사양서(단일 진실 공급원) 참조 경로를 명시합니다 (`forgeflow doc list` 또는 `~/.local/forgeflow/current/lib/forgeflow/templates/spec/` 7대 사양서).
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

5. 릴리즈 수명주기 디렉터리 스캐폴딩:
   - `tasks/in-progress/` 및 `tasks/completed/` 디렉터리를 생성합니다.
   - `tasks/README.md`에 비-행동지침 경계 선언을 작성합니다.

6. 세션 진입점 앵커(AGENTS.md / CLAUDE.md) 비파괴적 주입:
   - 리포지토리 루트의 `AGENTS.md` (또는 `CLAUDE.md`)에 `<!-- forgeflow:boot-anchor:start -->` 주석 마커 블록으로 부팅 시퀀스를 주입하여 AI 에이전트가 작업 전 헌법과 공식 사양서를 자동 인지하도록 합니다. 기존 사용자 내용은 100% 보존됩니다.

7. 완료 보고:
   - 셋업 완료 상태를 요약하고, 다음 시작 명령어(`/speckit.specify "기능 설명"`)를 안내합니다.
EOF

# 2. update-forgeflow 스킬 설치
UPDATE_DIR="${SKILLS_ROOT}/update-forgeflow"
mkdir -p "${UPDATE_DIR}"

cat << 'EOF' > "${UPDATE_DIR}/SKILL.md"
---
name: update-forgeflow
description: Updates ForgeFlow globally and migrates governance configurations, constitution, and hooks in an existing repository.
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
   - 이 명령은 `tasks/in-progress/` 및 `tasks/completed/` 내부의 모든 작업 산출물을 100% 보존하면서 `.forgeflow.json`, `.specify/scripts/bash/`(0o755 실행 권한 포함), 템플릿, 헌법, 훅, 및 `AGENTS.md` 세션 진입점 앵커를 최신 표준으로 동기화합니다.
2. 거버넌스 무결성 검증:
   - `forgeflow check --quiet` 명령을 실행하여 마이그레이션 후 거버넌스 무결성을 검증합니다.
3. 결과 보고:
   - 전역 런타임 업그레이드 여부, 로컬 리포지토리 사양 갱신 내역 및 버전 정보, 정합성 검증 결과를 사용자에게 명확히 보고합니다.
EOF

chmod +x "${SETUP_DIR}/SKILL.md" "${UPDATE_DIR}/SKILL.md" 2>/dev/null || true
echo "[PASS] setup-forgeflow 및 update-forgeflow 스킬이 ${SKILLS_ROOT}/ 에 성공적으로 설치되었습니다."
