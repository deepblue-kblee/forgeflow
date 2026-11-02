#!/usr/bin/env bash
# Generate ForgeFlow skills from the same distribution as the CLI/specs.
set -euo pipefail

SKILLS_ROOT="${FORGEFLOW_SKILLS_DIR:-${HOME}/.agents/skills}"
mkdir -p "$SKILLS_ROOT"

# Optional external planning tools. Core runtime remains Python stdlib only.
if [ "${FORGEFLOW_INSTALL_SPECKIT_SKILLS:-0}" = "1" ]; then
  if ! command -v npx >/dev/null 2>&1; then
    echo "[ERROR] Explicit Spec Kit skill installation requires npx." >&2
    exit 1
  fi
  npx -y skills add -g dceoy/speckit-agent-skills \
    -s speckit-specify -s speckit-clarify -s speckit-plan \
    -s speckit-tasks -s speckit-implement -s speckit-constitution \
    -s speckit-analyze -y
fi

SETUP_DIR="$SKILLS_ROOT/setup-forgeflow"
UPDATE_DIR="$SKILLS_ROOT/update-forgeflow"
FORGEFLOW_DIR="$SKILLS_ROOT/forgeflow"
GRAPHIFY_DIR="$SKILLS_ROOT/forgeflow-graphify"
mkdir -p "$SETUP_DIR" "$UPDATE_DIR" "$FORGEFLOW_DIR" "$GRAPHIFY_DIR"

cat << 'EOF' > "$SETUP_DIR/SKILL.md"
---
name: setup-forgeflow
description: 현재 프로젝트에 사용자 설정을 보존하는 ForgeFlow 진입점과 선택적 Spec Kit 지원을 구성합니다.
---

# setup-forgeflow

현재 저장소에 ForgeFlow의 기본 경량 흐름을 구성합니다.

1. 현재 repository와 사용자 지침, .forgeflow/config.json, 진행 중 workflow/strict package를 확인합니다. setup 권한을 전역 upgrade/자료 삭제로 확대하지 않습니다.
2. forgeflow CLI가 있으면 forgeflow init --speckit을 실행합니다. Spec Kit 로컬 support가 필요 없는 기본 초기화는 forgeflow init을 사용합니다.
3. 기존 사용자 설정, constitution, hooks, templates와 진행/완료 evidence를 보존합니다. 생성일에 따른 폐기나 사용자 문서 교체를 하지 않습니다. 설정을 수동으로 덮어써 CLI의 보존 동작을 우회하지 않습니다.
4. 프로젝트 test/lint/build의 실제 argv commands를 workflow.checks에 연결합니다. 빈 기본값이나 항상 성공하는 placeholder는 검증이 아닙니다.
5. .forgeflow/spec/README.md에서 새 작업의 계약을 확인합니다. 실행 중 작업은 state의 baseline.command와 baseline.path/spec를 유지합니다. 여러 task의 기준이 다르면 project 기본 링크나 identity 없는 launcher로 대체하지 않습니다.
6. 구성 결과와 필요한 프로젝트 검증 명령을 보고합니다. 작은 변경에 다중 Gate 문서나 seal을 요구하지 않습니다.

Spec Kit 외부 스킬은 필요할 때 설치 범위를 확인합니다. 설치 스크립트의 외부 자동 설치는 FORGEFLOW_INSTALL_SPECKIT_SKILLS=1 opt-in입니다. Core는 Python 3.10+ 표준 라이브러리로 동작합니다.
EOF

cat << 'EOF' > "$UPDATE_DIR/SKILL.md"
---
name: update-forgeflow
description: 진행 중 작업의 기준을 유지하고 사용자 설정을 보존하며 ForgeFlow 프로젝트 통합을 갱신합니다.
---

# update-forgeflow

1. 요청한 범위가 전역 upgrade인지 프로젝트 update인지 확인하고 이미 받은 권한을 재사용합니다. 현재 project/active task baseline을 먼저 읽습니다.
2. forgeflow upgrade --check --json으로 가용 version, source revision, source identity, identity_comparison을 읽습니다. 전역 변경이 승인된 범위일 때만 forgeflow upgrade --revision <ref>를 실행합니다. 새 버전이 있다는 사실만으로 자동 설치하지 않습니다.
3. forgeflow update --dry-run --json으로 created/updated/removed/preserved/conflicts/blockers를 먼저 확인합니다. 그다음 forgeflow update --json으로 적용합니다. 사용자 config/constitution/hooks/templates와 historical evidence를 보존하며 --force를 보존 우회 수단으로 사용하지 않습니다.
4. status needs-action이면 파일을 쓰지 않은 상태입니다. blocker의 task/baseline/pinned command 또는 conflict path를 확인하고, 지정된 conflict만 forgeflow update --accept <path>로 해소합니다. 하나의 --force로 전체 보호를 해제하지 않습니다.
5. upgrade 성공은 installer exit 0이 아니라 실제 package metadata, source revision/identity, entrypoint version, spec, 생성 skills 검증으로 판단합니다. 검증 실패는 성공으로 보고하지 않습니다.
6. 활성 workflow나 strict package 때문에 update가 차단되면 해당 작업의 pinned runtime을 계속 사용합니다. state/evidence를 삭제해서 차단을 없애지 않습니다.
7. 새 기준을 채택하는 작업은 영향 검토 후 forgeflow workflow adopt <id> --reason "이유" --impact "영향 검토"를 실행합니다. 기존 권한을 확장하지 않고 영향받는 검증만 갱신합니다. strict package policy migration은 별도 적용 범위를 검토합니다.
8. 실제 변경 파일, 이전/새 distribution 및 project runtime identity, 적용된 검증과 남은 작업을 보고합니다. 버전 문자열만으로 같은 배포라고 단정하지 않습니다.

공식 계약: .forgeflow/spec/DISTRIBUTION_SPEC.md. 생성 skills와 runtime/spec/templates는 같은 배포 단위로 전달됩니다.
EOF

cat << 'EOF' > "$FORGEFLOW_DIR/SKILL.md"
---
name: forgeflow
description: 요구사항·계획·구현·프로젝트 검증·허용된 통합·정리까지 책임지고 조정하는 ForgeFlow 개발 흐름입니다.
---

# forgeflow

사용자가 맡긴 개발 작업을 허용된 완료 지점까지 조정합니다. Spec Kit에 계획/태스크, 프로젝트 도구에 검증, Git/owning host에 repository operations를 위임합니다.

## 시작과 계획

1. repository 지침, docs/session-state/next-actions.md(존재 시), .forgeflow/config.json을 읽습니다. 새 작업의 기본 진입점은 .forgeflow/spec/README.md입니다. 재개는 task state의 baseline.command에 doc show를 붙이거나 baseline.path/spec를 읽어 해당 task의 기준을 확인합니다. 여러 task의 identity가 다르면 project 기본 spec 링크로 대체하지 않습니다. 이미 받은 승인은 재사용합니다.
2. 질의/설명/상태 조회는 변경 workflow를 만들지 않습니다. 작은 변경은 짧은 계획, 큰 변경은 필요한 Spec Kit specify/clarify/plan/tasks를 사용합니다.
3. 구현 전 scope, observable acceptance, plan, checks를 확정합니다. agreement에 owner(standalone|host), source/target, integration(none|local|pr), permissions, remote, task_owned_branch, include_existing_changes를 기록합니다. checks는 argv arrays입니다.
4. forgeflow workflow start <id> --agreement agreement.json으로 시작하고 forgeflow workflow check <id>로 구현 준비를 확인합니다. 공통 --repo-root와 --json을 사용할 수 있습니다. .forgeflow/workflows/<id>.json이 실행 상태의 단일 근거입니다.

## 구현과 검증

5. 합의 범위에서 구현하고 실패 원인을 고쳐 affected checks를 재실행합니다. acceptance를 임의 완화하지 않습니다. 반복 조사에도 no-progress budget을 적용하고 동일 증거를 무한 재조회하지 않습니다.
6. forgeflow workflow verify <id>로 실제 project/task checks를 실행합니다. project workflow.checks를 task에서 제거하지 않습니다. verification_paths는 필요한 구현/dependency 입력을 포함해야 합니다. 미선언 시 all-tracked 검사를 사용하며 scope 밖의 미commit dependency는 통합 전에 해소해야 합니다. 실제 무관한 문서/상태 변경만 명시적으로 입력에서 제외할 수 있습니다. AST review/raw Warning 0은 프로젝트가 선택한 경우에만 필수입니다.
7. 변경 동작, 실제 연결과 전달되는 entrypoint를 검증합니다. 코드/환경/통합 결과가 바뀌지 않았으면 같은 검증을 단계마다 반복하지 않습니다.

## 통합·정리·재개

8. forgeflow workflow finalize <id>는 기록된 권한 안에서만 실행합니다. commit은 task scope만, push/merge/delete-branch/host-cleanup은 각각 위임이 필요합니다. readiness만으로 실행 권한을 추정하지 않습니다.
9. host-owned checkout에서는 legacy auto_create_branch가 true여도 추가 branch/worktree를 만들지 않습니다. Project workflow.owner=host를 agreement의 standalone으로 덮어쓰지 않습니다. host pending action을 해당 도구로 수행하고 forgeflow workflow finalize <id> --receipt host-receipt.json으로 실제 결과를 연결합니다. 수행하지 않은 host cleanup을 성공으로 쓰지 않습니다.
10. standalone local merge는 PR 없이 가능합니다. pr route는 owner=host에서만 지원합니다. 즉시 source/target/검증 freshness를 확인합니다. 관련 없는 dirty 파일을 commit/reset/stash하지 않습니다. task-owned 대상만 정리합니다.
11. merge 성공 후 cleanup 실패 시 integrated 결과를 보존하고 cleanup만 재개합니다. forgeflow workflow status <id>를 확인하고 ready/integrated/cleaned 및 요청된 endpoint 달성 여부를 구분해 보고합니다. 완료 시 owning checkpoint를 갱신합니다.

새 권한/외부 승인/중대한 미정 사항이 있을 때만 해당 작업을 막고 구체적으로 확인합니다. 이미 받은 전체 승인을 반복 요청하지 않습니다. runtime mismatch는 baseline.command의 python3 .forgeflow/run.py --runtime-identity <digest> 명령으로 해당 task 기준을 실행하거나, 명시적 이유/영향 검토 후 adopt합니다.

## 명시적 strict compatibility

기존 strict package는 선택한 git-sha 또는 sha-free 정책을 유지하며 historical completed evidence는 수정하지 않습니다. 기본 workflow에 strict 문서를 강제하지 않습니다.

strict 순서: required Gate 1 evidence → 구현/필수 검증/QA_SIGNOFF.md → package-review → RELEASE_SIGNOFF.md/manifest 준비와 필요한 사용자 승인 → seal → complete.

- git-sha: forgeflow lifecycle package-review <id> <qa-sha>; 준비된 RELEASE_SIGNOFF.md 후 forgeflow lifecycle seal <id> <candidate-sha>.
- sha-free: forgeflow lifecycle package-review <id> --sha-free; 준비된 RELEASE_SIGNOFF.md 후 forgeflow lifecycle seal <id> --sha-free.
- 두 경로 모두 forgeflow lifecycle complete <id>로 패키지를 완료합니다. strict seal의 clean-worktree/manifest 조건을 사전에 확인합니다. 사용자 작업을 몰래 정리해 조건을 맞추지 않습니다.
- strict package 완료도 Git merge/delete 권한이나 실제 완료를 뜻하지 않습니다.

정확한 계약은 .forgeflow/spec/FLOW_SPEC.md, GATES_AND_LOOPS.md, DISTRIBUTION_SPEC.md에 있습니다.
EOF

cat << 'EOF' > "$GRAPHIFY_DIR/SKILL.md"
---
name: forgeflow-graphify
description: 사용 가능한 Graphify AST·의존성 지도로 코드 구조를 좁혀 탐색합니다.
---

# forgeflow-graphify

넓은 architecture/dependency 질문에 Graphify 지도를 사용하고 연결된 파일·심볼만 선별해 읽습니다. 정확한 파일/심볼 질문은 targeted rg와 focused reads로 바로 확인할 수 있습니다.

1. command -v graphify로 가용성을 확인합니다. 없으면 선택 도구 설치를 강요하거나 전체 작업을 차단하지 말고 focused source inspection으로 이어갑니다.
2. graphify-out/graph.json이 없으면 graphify extract <repo> --code-only를 사용합니다. 필요할 때 graphify update <repo>로 갱신합니다.
3. graphify explain "<symbol>" --graph graphify-out/graph.json 또는 graphify path "<source>" "<target>" --graph graphify-out/graph.json으로 연결을 좁힙니다.
4. 필요한 코드를 읽어 지도 결과를 검증합니다. 시각화가 필요하면 graphify export html을 사용할 수 있습니다.

도구 설치/외부 API 호출은 사용자가 허용한 범위를 따릅니다. Graphify는 ForgeFlow core runtime dependency가 아닙니다.
EOF

echo "[PASS] ForgeFlow skills generated in $SKILLS_ROOT"
