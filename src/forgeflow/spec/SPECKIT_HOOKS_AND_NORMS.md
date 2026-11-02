# Spec Kit 연결 규칙

Spec Kit은 규모 있는 요구사항·계획·태스크 작업을 위한 계획 도구입니다. 작은 작업에는 짧은 agreement plan을 사용할 수 있습니다.

## 선택적 흐름

```text
speckit-specify → speckit-clarify(필요 시) → speckit-plan → speckit-tasks → speckit-analyze(필요 시)
  → speckit-implement
  → forgeflow workflow verify
```

- `speckit-specify`: 요구사항과 acceptance
- `speckit-clarify`: 모호한 부분 보완
- `speckit-plan`: 구현 계획
- `speckit-tasks`: 의존성 순서의 태스크
- `speckit-analyze`: spec/plan/tasks 일관성 검토
- `speckit-implement`: `tasks.md` 실행

`speckit-implement`는 `tasks.md`가 있는 작업에서 사용합니다. 작은 변경은 직접 구현할 수 있습니다. Spec Kit 실행도 ForgeFlow agreement의 scope, checks, permissions를 넘지 않습니다.

## Design checkpoint

`workflow start --hitl design`을 사용하면 `workflow check` 후 사용자가 spec/plan/tasks와 acceptance를 검토합니다.

```bash
forgeflow workflow continue <id> --note "설계 승인"
forgeflow workflow revise <id> --note "수정 요청"
forgeflow workflow stop <id> --note "보류"
```

기본 `auto` mode에서는 checkpoint 없이 구현으로 진행합니다.

## 로컬 support

`forgeflow init --speckit`은 누락된 scripts/templates를 구성할 수 있습니다. 기존 project constitution·hooks·command overrides·templates는 보존합니다.

Support scripts는 명시적 feature state를 해석하고 계획 자산을 만듭니다. 번들 `create-new-feature.sh`는 독자적으로 Git branch를 만들지 않습니다. Feature identifier는 branch 생성·전환·merge·삭제 권한을 뜻하지 않습니다.

## 실행과 완료

- `tasks.md`는 구현 진행을 기록합니다.
- commit은 권한과 task scope를 따릅니다.
- Checkbox마다 commit을 강제하거나 실패 시 사용자 작업을 자동 reset/revert하지 않습니다.
- Spec Kit command 완료는 merge/cleanup을 증명하지 않습니다.
- 검증은 `forgeflow workflow verify`, 통합은 `workflow finalize`가 소유합니다.
