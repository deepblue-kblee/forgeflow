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

## 작업 단위와 재개·대체

독립적으로 검증·완료할 수 있는 결과 하나를 workflow 하나로 관리합니다. 같은 결과를 위한 계획 보완은 기존 workflow에서 처리하고, 실제 실행과 검증·종료 기록을 같은 경로로 연결합니다.

### Workflow 단위 선택 기준

- 배포 가능한 결과 또는 비코드 작업의 독립적인 인수 결과 하나를 workflow 하나로 묶습니다.
- 조사·구현·테스트·문서는 그 결과의 내부 단계이며, 단계마다 새 workflow를 만들지 않습니다.
- 기존 작업과 독립적으로 인수·배포·보류할 수 있는 결과가 추가되면 분리를 검토합니다.
- 한 workflow의 완료 조건에 당장 끝낼 수 있는 장애 복구와 장기 기능 개발을 함께 넣지 않습니다.
- 작은 작업에는 짧은 agreement/plan을 허용하며 Spec Kit의 모든 산출물을 일괄 강제하지 않습니다.
- 기존 변경의 단순 commit/push 요청은 [활성화 조건](#활성화-조건)을 따릅니다.

| 요청 | 권장 단위 |
| --- | --- |
| 운영 명령 장애 복구 및 검증된 배포 | 복구 결과를 소유하는 workflow 하나 |
| 복구 과정에서 확인된 별도 장기 기능 | 후속 결과로 분리하고 관계 연결 |
| 같은 결과의 설계 누락 수정·테스트 보완 | 기존 workflow에서 계획 보완 |
| 자동 report와 별도 원문 writer | 각각 독립 인수가 가능하면 별도 workflow |
| 문서 개선만 요청 | 해당 문서 결과에 비례한 workflow; 불필요한 배포 단계 없음 |

### 재개·수정·분리·대체 선택표

- 같은 목표, 구현 진행 중 → 기존 workflow 재개.
- 같은 목표, scope/plan/checks 보완 → 기존 workflow의 agreement 수정 경로 사용.
- 독립적인 목표 추가 → 새 workflow 및 관계 연결.
- 기존 계획 폐기 후 다른 계획으로 진행 → 기존 기록을 대체됨으로 보존하고 후속 연결.
- 유효한 완료 기록 이후 새 변경 발생 → 과거 완료 증거를 보존하고 새 작업과 구분.
- 검증 stale → 변경된 입력과 필요한 검증 확인; 새 workflow를 기본 해결책으로 제시하지 않음.

### 실행 경로와 승인 재사용

- 개발 중 focused checks와 최종 `workflow verify`의 역할을 구분합니다.
- 최종 검증·종료는 `verify → finalize`로 연결하여 중복 실행과 별도 상태 기록을 줄입니다.
- 이미 받은 승인 중 현재 저장소·대상·operation 범위에 유효한 것은 재사용합니다. 기록 누락을 승인 부재로 단정하지 않습니다.
- 메타데이터를 기록하기 위해 요청 범위 밖 추가 commit을 자동 생성하지 않습니다.
- 상태 정리만을 위한 새 spec 작성, runtime 교체, 전체 회귀 재실행을 기본 절차로 요구하지 않습니다.

### 상태 해석 주의

- `planned`는 "아직 최종 검증 기록 없음"이며 구현 미착수 여부를 판단할 근거가 아닙니다.
- `ready`는 검증 통과를 뜻하며 전체 제품 인수 완료를 뜻하지 않습니다.
- `initial_head`와 현재 HEAD의 차이는 오류가 아닙니다.
- acceptance 진행 요약은 명시된 결과·증거가 있을 때만 제공하고, 테스트 PASS나 AI 추론만으로 전체 acceptance를 자동 완료하지 않습니다.

## 재개와 baseline

Active task는 content identity와 실행 가능한 `.forgeflow/runtime/<digest>/forgeflow/` snapshot을 유지합니다. Global current가 바뀌어도 task state의 `baseline.command`로 같은 기준을 실행합니다. 기준 변경은 영향 검토 후 `workflow adopt <id> --reason ... --impact ...`로 명시합니다.

## 과거 버전

0.1.x strict lifecycle, Gate 1/2/3, QA-SHA, package seal, lifecycle audit은 0.2.x 기본 flow가 아닙니다. 과거 artifact는 `archive/pre-0.2.0` tag에 보존하며, 0.1.x project는 별도 `forgeflow-migrate` 도구로 정리한 뒤 0.2.x로 전환합니다.
