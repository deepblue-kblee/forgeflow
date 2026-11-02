#!/usr/bin/env bash
# Generate ForgeFlow 0.2.x skills from the same distribution as the CLI/specs.
set -euo pipefail

SKILLS_ROOT="${FORGEFLOW_SKILLS_DIR:-${HOME}/.agents/skills}"
mkdir -p "$SKILLS_ROOT"

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
description: 현재 프로젝트에 0.2.x lean workflow와 선택적 Spec Kit 지원을 구성합니다.
---

# setup-forgeflow

1. repository 지침과 `.forgeflow/config.json`을 확인하고, 기존 사용자 파일을 보존합니다.
2. `forgeflow init`으로 lean project를 구성하거나 `forgeflow init --speckit`으로 Spec Kit scripts/templates를 추가합니다.
3. 프로젝트의 실제 test/lint/build argv를 `workflow.checks`에 연결합니다. 빈 checks나 항상 성공하는 placeholder를 사용하지 않습니다.
4. `tasks/`를 만들지 않습니다. 실행 상태는 `.forgeflow/workflows/<id>.json`, 현재 사양서는 `.forgeflow/spec/`입니다.
5. 0.1.x `tasks/`, `docs/releases/`, strict lifecycle 자산이 있으면 직접 삭제하지 말고 `forgeflow-migrate`를 안내합니다.
EOF

cat << 'EOF' > "$UPDATE_DIR/SKILL.md"
---
name: update-forgeflow
description: 현재 0.2.x 프로젝트의 설정과 runtime을 갱신하고 legacy project는 migration tool로 안내합니다.
---

# update-forgeflow

1. `forgeflow upgrade --check --json`으로 version, revision, source identity를 확인합니다. 승인된 범위에서만 `forgeflow upgrade --revision <ref>`를 실행합니다.
2. `forgeflow update --dry-run --json`으로 변경 예정 파일을 확인하고 `forgeflow update --json`으로 적용합니다.
3. `update`가 `needs-action`과 legacy-project blocker를 반환하면 파일을 임의로 지우지 말고 별도 `forgeflow-migrate` 도구를 안내합니다.
4. upgrade 성공은 installer exit 0이 아니라 실제 package metadata, entrypoint version, spec, 생성 skills probe로 판단합니다.
5. active workflow가 있으면 해당 task의 pinned baseline command를 유지합니다.
EOF

cat << 'EOF' > "$FORGEFLOW_DIR/SKILL.md"
---
name: forgeflow
description: 설계 검토 checkpoint를 선택적으로 두는 lean 개발 workflow를 조정합니다.
---

# forgeflow

## 시작

1. repository 지침, `.forgeflow/config.json`, `.forgeflow/spec/README.md`를 읽습니다.
2. scope, acceptance, plan, checks, owner, source/target, integration, permissions를 agreement JSON에 기록합니다.
3. `forgeflow workflow start <id> --agreement agreement.json`으로 시작합니다.
4. 설계 검토가 필요하면 `--hitl design`을 추가합니다.

## 설계와 선택적 checkpoint

5. 큰 작업은 Spec Kit `speckit-specify → clarify → plan → tasks → analyze`를 사용합니다.
6. `speckit-implement`는 `tasks.md`가 있는 구현 단계에서 사용합니다. 작은 변경은 직접 구현할 수 있습니다.
7. `forgeflow workflow check <id> --summary "<요약>" ...`로 구현 준비를 확인합니다.
8. `--hitl design`이면 state가 `awaiting-user`로 멈춥니다. 사용자는 `workflow continue`, `workflow revise --note`, `workflow stop --note` 중 하나를 선택합니다. 기본 auto mode에서는 멈추지 않습니다.

## 구현과 검증

9. agreement scope 안에서 구현하고 실패 원인을 수정한 뒤 영향받는 checks를 다시 실행합니다.
10. `forgeflow workflow verify <id>`로 프로젝트 checks를 실행합니다. project checks를 제거하거나 acceptance를 임의 완화하지 않습니다.
11. `forgeflow workflow finalize <id>`는 기록된 권한 안에서만 commit/push/merge/cleanup을 수행합니다. host-owned checkout은 owning tool에 위임하고 receipt로 결과를 연결합니다.

## 원칙

- `.forgeflow/workflows/<id>.json`이 실행 상태의 단일 근거입니다.
- active task는 pinned runtime/spec baseline을 유지합니다.
- 사용자 변경, unrelated dirty work, historical evidence를 임의로 삭제하지 않습니다.
- 0.1.x strict lifecycle/audit 명령은 0.2.x의 선택지가 아닙니다.
EOF

cat << 'EOF' > "$GRAPHIFY_DIR/SKILL.md"
---
name: forgeflow-graphify
description: 사용 가능한 Graphify AST·의존성 지도로 코드 구조를 좁혀 탐색합니다.
---

# forgeflow-graphify

1. `command -v graphify`로 가용성을 확인합니다. 없으면 focused source inspection으로 이어갑니다.
2. `graphify-out/graph.json`이 없으면 `graphify extract <repo> --code-only`를 사용합니다.
3. `graphify explain "<symbol>" --graph graphify-out/graph.json` 또는 `graphify path "<source>" "<target>" --graph graphify-out/graph.json`으로 연결을 좁힙니다.
4. 필요한 코드를 읽어 지도 결과를 검증합니다.

Graphify는 ForgeFlow core runtime dependency가 아닙니다.
EOF

echo "[PASS] ForgeFlow skills generated in $SKILLS_ROOT"
