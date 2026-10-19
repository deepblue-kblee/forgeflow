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

## 실행 절차

1. 필수 도구 및 Spec Kit 스킬 자동 점검/설치:
   - 시스템에 `forgeflow` CLI가 설치되어 있는지 확인합니다 (`command -v forgeflow`).
   - `~/.agents/skills/`에 `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-implement` 스킬이 설치되어 있는지 확인합니다.
   - 누락된 Spec Kit 스킬이 있을 경우 에이전트가 다음 명령을 실행하여 자동으로 설치를 완료합니다 (이미 설치되어 있으면 건너뜁니다):
     ```bash
     npx -y skills add -g dceoy/speckit-agent-skills -s speckit-specify -s speckit-clarify -s speckit-plan -s speckit-tasks -s speckit-implement -s speckit-constitution -s speckit-analyze -y
     ```

2. 거버넌스 설정 파일 생성:
   - 프로젝트 루트에 `.forgeflow.json` 파일을 생성합니다.
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

3. Spec Kit 헌법 및 강제 훅 주입:
   - `.specify/memory/constitution.md` 파일을 생성하여 5대 불변 거버넌스 헌법을 선언합니다.
     - 제1조 (무승인 구현 금지 - No Code Before Gate 1): `tasks/in-progress/<id>/GATE1_REVIEW.md` 승인 전 소스 코드 작성/수정 절대 금지.
     - 제2조 (가짜 멈춤 금지 - No False Stopping): 단순 테스트 실패, 린트 오류 시 사용자에게 턴을 넘기지 않고 내부 자가 치유 루프(Loop 2) 자율 완주.
     - 제3조 (원자적 루프 정의 - Atomic Remediation Unit): 1회 루프는 `원인 식별 -> 1개 수정 -> 테스트 재실행 -> git commit`으로 완결.
     - 제4조 (루프 예산 및 진짜 멈춤 - Loop Budget & True Stop): 동일 오류 5회 연속 무진전 시에만 작업 중단 및 사용자 에스컬레이션.
     - 제5조 (스펙 무단 하향 금지 - No Spec Downgrade): 구현 난항을 이유로 `spec.md` 무단 축소 금지, 필요 시 Gate 1 재승인(Loop 3) 수행.
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

4. 릴리즈 수명주기 디렉터리 스캐폴딩:
   - `tasks/in-progress/` 및 `tasks/completed/` 디렉터리를 생성합니다.
   - `tasks/README.md`에 비-행동지침 경계 선언을 작성합니다.

5. 완료 보고:
   - 셋업 완료 상태를 요약하고, 다음 시작 명령어(`/speckit.specify`)를 안내합니다.
EOF

# 2. update-forgeflow 스킬 설치
UPDATE_DIR="${SKILLS_ROOT}/update-forgeflow"
mkdir -p "${UPDATE_DIR}"

cat << 'EOF' > "${UPDATE_DIR}/SKILL.md"
---
name: update-forgeflow
description: Updates and migrates ForgeFlow governance configurations, constitution, and hooks in an existing repository.
---

# update-forgeflow

기존 리포지토리의 ForgeFlow 설정(`.forgeflow.json`)과 Spec Kit 규범 주입 파일들을 최신 버전 규격에 맞게 갱신하고 마이그레이션합니다.

## 실행 절차

1. 버전 차이 분석:
   - 현재 프로젝트 루트의 `.forgeflow.json`에 명시된 버전과 설치된 전역 `forgeflow` CLI 버전을 대조합니다.
   - 버전이 동일하고 파일 변경이 없으면 불필요한 갱신을 생략합니다.

2. 기존 데이터 보존 확인:
   - `tasks/in-progress/` 및 `tasks/completed/` 디렉터리의 진행 중/완료된 릴리즈 아티팩트는 일절 삭제하거나 덮어쓰지 않습니다.

3. 설정 및 스키마 마이그레이션:
   - `.forgeflow.json`의 스키마 필드를 신규 버전 규격에 맞추어 보정하고 버전을 갱신합니다.
   - `.specify/extensions.yml`의 훅 정의를 최신 CLI 서브커맨드 규격으로 갱신합니다.
   - `.specify/memory/constitution.md`의 거버넌스 헌법 조항을 최신 규정으로 동기화하되, 사용자가 수동으로 추가한 커스텀 규칙이 있을 경우 안전하게 보존·병합합니다.
   - `.specify/templates/commands/` 템플릿을 최신 버전으로 갱신합니다.

4. 호환성 검증:
   - `forgeflow check --quiet` 명령을 실행하여 마이그레이션 후 거버넌스 정합성을 검증합니다.

5. 마이그레이션 결과 보고:
   - 갱신된 버전 정보, 수정된 설정 파일 목록, 검증 통과 여부를 사용자에게 간결히 보고합니다.
EOF

chmod +x "${SETUP_DIR}/SKILL.md" "${UPDATE_DIR}/SKILL.md" 2>/dev/null || true
echo "[PASS] setup-forgeflow 및 update-forgeflow 스킬이 ${SKILLS_ROOT}/ 에 성공적으로 설치되었습니다."
