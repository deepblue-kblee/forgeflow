# ForgeFlow

ForgeFlow는 AI 에이전트의 개발 작업을 설계·구현·검증·통합·정리까지 조정하는 lean workflow입니다. 기본은 자동 진행이며, 원할 때 디자인 종료 지점에서 사용자가 직접 설계를 검토할 수 있습니다.

## 설치

```bash
./install.sh
# 또는
FORGEFLOW_SKILLS_DIR=~/.agents/skills ./install.sh
```

## 시작

```bash
forgeflow init
forgeflow init --speckit
```

`init --speckit`은 Spec Kit scripts/templates를 추가합니다. `tasks/` 디렉터리는 만들지 않으며 실행 상태는 `.forgeflow/workflows/<id>.json`에 저장됩니다.

## 기본 flow

```text
agreement 작성
  → workflow start
  → Spec Kit 설계(specify/clarify/plan/tasks)
  → workflow check
  → [선택적 design checkpoint]
  → 구현(speckit-implement 또는 직접)
  → workflow verify
  → workflow finalize
```

```bash
forgeflow workflow start example --agreement agreement.json
forgeflow workflow check example --json
forgeflow workflow verify example --json
forgeflow workflow finalize example --json
```

## 선택적 design checkpoint

설계가 끝난 지점에서만 멈춥니다.

```bash
forgeflow workflow start example --agreement agreement.json --hitl design
forgeflow workflow check example --summary "spec/plan/tasks 요약"
forgeflow workflow continue example --note "설계 승인"
# 또는
forgeflow workflow revise example --note "수정 요청"
forgeflow workflow stop example --note "보류"
```

기본 `auto` mode에서는 멈추지 않고 끝까지 진행합니다. checkpoint decision은 workflow state에 기록됩니다.

## Spec Kit

큰 작업은 다음 순서를 사용할 수 있습니다.

```text
speckit-specify → speckit-clarify → speckit-plan → speckit-tasks → speckit-analyze
  → speckit-implement → forgeflow workflow verify
```

작은 작업은 Spec Kit 없이 agreement plan과 checks로 처리할 수 있습니다.

## Update와 upgrade

```bash
forgeflow update --dry-run --json
forgeflow update --json
forgeflow upgrade --check --json
forgeflow upgrade --revision <ref>
```

`update`는 현재 0.2.x project를 갱신합니다. 0.1.x `tasks/`, `docs/releases/`, strict lifecycle layout은 자동 변환하지 않고 `needs-action`으로 안내합니다. 해당 project는 별도 `forgeflow-migrate` 도구로 정리합니다.

## 원칙

- 프로젝트 checks가 검증의 기준입니다.
- commit/push/merge/cleanup은 agreement의 permissions를 따릅니다.
- 사용자 변경과 unrelated dirty work를 임의로 삭제하지 않습니다.
- active task는 content-addressed runtime/spec baseline으로 고정됩니다.
- 과거 0.1.x strict lifecycle/audit은 현행 flow가 아니며 `archive/pre-0.2.0` tag에 보존됩니다.

공식 계약은 [docs/spec/README.md](docs/spec/README.md)에서 확인할 수 있습니다.
