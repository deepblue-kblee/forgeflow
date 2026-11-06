# ForgeFlow 저장소 작업 지침

## 목적과 단일 기준

ForgeFlow 0.2.x는 요구사항·설계·구현·검증·허용된 통합·정리를 단일 workflow state로 조정합니다. 기본은 auto 진행이며, 사용자가 요청한 경우 디자인 종료 지점에서 한 번만 멈춥니다.

- 실행 상태: `.forgeflow/workflows/<id>.json`
- 현재 사양서: `docs/spec/` 편집 원본, `src/forgeflow/spec/` 기계적 복제본
- 세션 checkpoint: `docs/session-state/next-actions.md`
- Core runtime: Python 3.10+ 표준 라이브러리만 사용

## 활성화 경계

ForgeFlow workflow는 **사용자가 ForgeFlow 사용을 명시적으로 요청했거나**, 현재 작업에서 `forgeflow` skill이 실제로 사용된 경우에만 적용합니다. 저장소에 `.forgeflow/` 설정이나 skill이 있고 과거 workflow가 있다는 사실만으로는 적용하지 않습니다.

- 이미 검토된 변경의 commit/push만 요청하면 새 workflow를 만들지 않고, 해당 작업의 권한과 저장소 정책에 따라 변경 경로를 확인한 뒤 commit/push와 결과 확인만 수행합니다.
- workflow·세션 상태 기록용 추가 커밋은 요청 범위에 포함되거나 프로젝트 정책이 직접 요구할 때만 생성합니다.
- ForgeFlow가 명시적으로 활성화된 경우에도 workflow와 완료 기록은 요청된 작업 범위에 비례해야 합니다.

## 기본 flow

```text
agreement → workflow start → Spec Kit 설계 → workflow check
  → [선택적 design checkpoint]
  → 구현(speckit-implement 또는 직접)
  → workflow verify → workflow finalize
```

- 구현 전 scope, acceptance, plan, checks를 agreement에 기록합니다.
- 검증은 프로젝트가 선언한 checks가 소유합니다.
- commit/push/merge/delete/cleanup은 기록된 permissions와 Git/host ownership을 따릅니다.
- readiness는 integration 권한이 아닙니다.
- 무관한 dirty 파일과 사용자 변경을 임의로 삭제·stage·stash·reset하지 않습니다.

## 작업 단위와 재개

- 독립적으로 검증·완료할 수 있는 결과 하나를 workflow 하나로 관리합니다. 조사·구현·테스트·문서는 내부 단계입니다.
- 같은 결과의 계획 보완은 기존 workflow에서 처리하고, 독립 목표가 추가될 때만 새 workflow를 만들어 관계를 연결합니다.
- 한 workflow의 완료 조건에 당장 끝낼 수 있는 장애 복구와 장기 기능을 함께 넣지 않습니다.
- `planned`는 미착수, `ready`는 제품 완료, `initial_head` 차이는 오류로 해석하지 않습니다.

## HITL design checkpoint

```bash
forgeflow workflow start <id> --agreement agreement.json --hitl design
forgeflow workflow check <id> --summary "<spec/plan/tasks 요약>"
forgeflow workflow continue <id> --note "승인"
forgeflow workflow revise <id> --note "수정 요청"
forgeflow workflow stop <id> --note "보류"
```

- 기본값은 auto이며 checkpoint 없이 끝까지 진행합니다.
- `--hitl design`일 때만 `awaiting-user`로 멈춥니다.
- 이후 구현·검증·통합·정리에는 추가 checkpoint가 없습니다.
- design checkpoint는 구현 전 spec/plan/tasks와 acceptance를 확인하는 용도입니다.

## Spec Kit

큰 작업은 `speckit-specify → clarify → plan → tasks → analyze → implement`를 사용할 수 있습니다. 작은 작업은 짧은 agreement plan으로 처리합니다. `speckit-implement`는 `tasks.md`가 있는 구현 단계의 실행 도구입니다.

Spec Kit은 계획·태스크 도구이며, 검증은 `forgeflow workflow verify`, repository operations는 Git/owning host가 소유합니다.

## 검증과 실패 처리

- 구현 중 focused 검사를 사용하고, 통합 전 필요한 관련 suite를 실행합니다.
- 코드·환경·통합 결과가 바뀌면 영향받는 검사를 다시 실행합니다.
- 결함을 숨기려고 테스트를 완화하지 않습니다.
- 동일 무진전 반복에는 설정된 no-progress budget(통상 5회)을 적용합니다.
- 외부 권한·필수 capability·중대한 사용자 결정이 없으면 해당 단계에서 막힐 수 있습니다.

## Runtime과 update

- Active task는 content-addressed runtime/spec/template baseline과 실행 snapshot을 유지합니다.
- 기준 변경은 `workflow adopt <id> --reason ... --impact ...`로 명시합니다.
- `forgeflow update`는 현재 0.2.x project만 갱신합니다.
- 0.1.x `tasks/`, `docs/releases/`, legacy `.forgeflow.json`, `.forgeflow/lifecycle`은 자동 변환하지 않고 `needs-action`과 `forgeflow-migrate` 안내를 반환합니다.
- User project migration은 별도 `forgeflow-migrate` 도구가 담당하며 core package에 포함하지 않습니다.

## 과거 버전

0.1.x strict lifecycle/audit, Gate 1/2/3, QA-SHA, package seal은 현행 선택지가 아닙니다. 과거 artifact와 code는 `archive/pre-0.2.0` tag에 보존하며 active 문서·CLI·skills에서 안내하지 않습니다.

## Handoff

작업 종료 전 `docs/session-state/next-actions.md`에 관찰된 진행·검증·미완·다음 행동을 기록합니다. 구현 완료·차단·미착수를 정확히 보고합니다.
