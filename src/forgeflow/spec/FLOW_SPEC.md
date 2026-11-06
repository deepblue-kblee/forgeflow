# ForgeFlow 개발 흐름

## 목적과 책임

ForgeFlow는 요구사항부터 설계·구현·검증·허용된 통합·정리까지 조정합니다. Spec Kit은 계획·태스크 도구, 프로젝트 명령은 검증, Git 또는 owning host는 repository operations를 담당합니다. Core는 Python 3.10+ 표준 라이브러리만 사용합니다.

## 활성화 조건

ForgeFlow workflow는 사용자가 ForgeFlow 사용을 명시적으로 요청했거나, 현재 작업에서 `forgeflow` skill이 실제로 사용된 경우에만 적용합니다.

- `.forgeflow/` 설정, 과거 workflow, skill 설치 사실만으로는 workflow를 시작하지 않습니다.
- 이미 검토된 변경의 commit/push만 요청하면 새 workflow를 만들지 않고, 해당 작업의 권한과 저장소 정책에 따라 변경 경로를 확인한 뒤 commit/push와 결과 확인만 수행합니다.
- workflow·세션 상태 기록용 추가 커밋은 요청 범위에 포함되거나 프로젝트 정책이 직접 요구할 때만 생성합니다.
- 명시적으로 활성화된 경우에도 workflow와 완료 기록은 요청된 작업 범위에 비례합니다.

## 기본 흐름

```text
agreement → workflow start → 설계 → workflow check
  → [선택적 design checkpoint]
  → 구현(speckit-implement 또는 직접)
  → workflow verify → workflow finalize
```

두 진행 조건을 유지합니다.

1. 구현 전 scope, 관찰 가능한 acceptance, 작업에 비례하는 plan, 필수 검증 명령을 확정합니다.
2. 통합 전 필요한 검증이 통과하고 해당 operation의 위임 권한이 기록돼 있어야 합니다.

## Agreement와 단일 상태

`forgeflow workflow start <id> --agreement <file.json>`로 시작합니다. 모든 workflow 명령은 `--repo-root`와 `--json`을 지원합니다. 실행 상태의 단일 근거는 `.forgeflow/workflows/<id>.json`입니다.

| 필드 | 의미 |
| --- | --- |
| scope | 작업이 소유하는 repository-relative 경로 |
| acceptance | 관찰 가능한 완료 조건 |
| plan | 구현 접근법 또는 Spec Kit 계획 참조 |
| checks | argv 배열 명령; 프로젝트 workflow.checks도 필수로 포함 |
| verification_note | 실행 검사가 필요 없는 변경의 구체적 근거 |
| verification_paths | 검증 입력 경로 |
| owner | `standalone` 또는 `host` |
| source, target | 정확한 branch |
| integration | `none`, `local`, `pr` |
| permissions | commit, push, merge, delete-branch, host-cleanup |
| remote | 명시한 remote |
| task_owned_branch | task가 source branch를 소유하는지 여부 |
| include_existing_changes | 시작 전 scoped 변경 포함 여부 |

## 선택적 design checkpoint

디자인 종료 지점 한 곳에서 사용자가 직접 확인할 수 있습니다.

```bash
forgeflow workflow start <id> --agreement agreement.json --hitl design
forgeflow workflow check <id> --summary "<설계 요약>"
forgeflow workflow continue <id> --note "승인"
forgeflow workflow revise <id> --note "수정 요청"
forgeflow workflow stop <id> --note "보류"
```

- 기본값은 `auto`이며 checkpoint 없이 끝까지 진행합니다.
- `--hitl design`일 때만 `check`가 `awaiting-user`로 멈춥니다.
- `continue`는 설계를 승인하고 구현 단계로 진행합니다.
- `revise`는 설계 수정 요청이며, 구현/검증 전 상태로 돌아갑니다.
- `stop`은 작업을 보류하고 state를 유지합니다.
- 이후 구현·검증·통합·정리에는 추가 checkpoint가 없습니다.

## 검증과 완료

- `workflow check`는 agreement와 구현 준비를 검증합니다.
- `workflow verify`는 project/task checks를 실행하고 결과를 state에 기록합니다.
- `workflow finalize`는 기록된 권한 안에서만 commit/push/merge/cleanup을 수행합니다.
- 상태는 `ready`, `integrated`, `cleaned`, `finalization_complete`로 구분합니다.
- readiness는 merge/push/delete 권한이 아닙니다.
- host-owned checkout은 owning tool이 작업하고 receipt로 결과를 연결합니다.
- 관련 없는 dirty 파일과 사용자 변경을 보존합니다.

## 재개와 baseline

Active task는 content identity와 실행 가능한 `.forgeflow/runtime/<digest>/forgeflow/` snapshot을 유지합니다. Global current가 바뀌어도 task state의 `baseline.command`로 같은 기준을 실행합니다. 기준 변경은 영향 검토 후 `workflow adopt <id> --reason ... --impact ...`로 명시합니다.

## 과거 버전

0.1.x strict lifecycle, Gate 1/2/3, QA-SHA, package seal, lifecycle audit은 0.2.x 기본 flow가 아닙니다. 과거 artifact는 `archive/pre-0.2.0` tag에 보존하며, 0.1.x project는 별도 `forgeflow-migrate` 도구로 정리한 뒤 0.2.x로 전환합니다.
