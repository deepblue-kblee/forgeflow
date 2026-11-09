# Workflow integrity guardrails — 해결 계획

대상 이슈: #27 (checkout별 단일 active writer + workflow 전환·종료 무결성)
검토 기준 커밋: `36999a82660fac5d60c128fc24b1dbb7a168f433` (현재 HEAD)

## 검증 결론

이슈의 문제 케이스 A·B·C·D와 요청 5는 모두 소스와 일치합니다. 오탐 없음.

- A. `start()`는 같은 ID만 차단하고 다른 active workflow 생성을 막지 않음 (`workflow.py:494-519`).
- B. `_classify`는 stopped/superseded를 active에서 제외하지만 `_active_work`(`scaffold.py:171-183`)와 `adopt`(`workflow.py:779-784`)는 그렇지 않음.
- C. `amend`/`stop`/`supersede`에 완료·대체·남은 cleanup guard 부재 (`workflow.py:607-657`, `797-831`).
- D. `supersede`가 후속 존재를 요구하므로 start guard와 함께 설계해야 교착이 없음 (`workflow.py:651-652`).

## 핵심 원칙

단일 lifecycle 판정을 만들고 모든 조회·mutation·update가 공유하게 한 뒤, 그 위에 writer guard와 원자적 전환을 얹는다.

## 설계

### 1. 단일 lifecycle 판정 (요청 4, B)

`workflow.py`에 표준 술어를 둔다. scaffold는 지연 import 또는 공통 모듈(`state.py`)로 공유.

```python
def _is_writer(state) -> bool:
    if state.get("superseded_by"):
        return False
    if state.get("finalization_complete"):
        return False
    return state.get("status") not in {
        "stopped", "superseded", "completed", "cleaned", "cancelled",
    }
```

- `_classify`, `_active_work`, `adopt` sibling 검사를 이 술어로 교체.
- `finalization_complete` 누락(옛 기록)은 보수적으로 active로 간주 (현행 `is not True` 의미 유지).

### 2. mutation guard (요청 3·4, C)

- `amend`: `finalization_complete` 또는 `superseded_by`면 거부 (완료/대체 기록은 역사 증거).
- `stop`: `finalization_complete`면 거부.
- `supersede`: `integration`이 있고 cleanup이 남았으면(`finalization_complete=False`) 거부.
- `stop`/`supersede`가 `pending`/`cleanup`을 지우지 않고 `ownership`/`obligations`로 보존, `status`/`list`에 표시.

### 3. start 단일 writer guard (요청 1, A)

- `start()`가 agreement 검증 뒤 `save()` 전에 같은 checkout(`repository` identity == `_identity(root)`)의 기존 writer를 스캔해 차단. 상태 파일 생성 전 거부가 핵심.
- blocker에 기존 ID·목표·상태·pinned command와 선택지(resume/amend, 후속 전환, 별도 branch/worktree) 표시. force 플래그 없음.
- checkout 단위 판정 (branch 전환은 우회로 인정하지 않음). read-only 조사·리뷰는 기존 workflow 아래에서만.

### 4. supersede에 통합한 원자적 전환 (요청 2, D)

`workflow supersede <old> --by <new> --reason ... [--agreement <file>]`:

- `--agreement` 제공 시: 단일 `locked()` 안에서 후속 `<new>` 생성 → `<old>`에 `superseded_by` 기록. 생성 시 같은 checkout의 다른 writer가 old뿐임을 보장(전환 대상인 old는 예외).
- `--agreement` 생략 시: `<new>`가 이미 존재해야 함 (기존 동작 유지).
- 재시도 안전: `<new>`가 이미 존재하면 id·baseline/agreement 일치 확인 후 재사용, 링크만 보완. 이미 superseded면 no-op.
- 순환·자기 참조·없는 후속은 기존 검사 유지.

### 5. old baseline 정리·updater 호환 (요청 5)

- `_is_writer` 전환으로 stopped/superseded 기록이 더 이상 update/init/adopt를 막지 않음.
- 관리용 dry-run(`workflow reconcile --dry-run`)으로 기록별 상태·소유 관계·권장 조치 표시. 공유 config/checks/launcher가 실제 충돌하는 항목만 보류. 기록 개수로 완료를 강제하지 않음.
- 신규 생성만 차단하고 기존 기록은 `list`/`status`/`resume`/`reconcile`로 조회·재개·정리 가능하게.

## 우선순위

- P0: 단일 판정, mutation guard, start writer guard, 원자적 전환.
- P1: old baseline 정리, updater 호환, dry-run 경로.

## 테스트·문서

- fixture 회귀: (1) 같은 checkout 이중 start 차단, (2) 전환 재시도 중복·관계 유실 없음, (3) 완료/대체 기록의 amend·stop·resume 거부, (4) cleanup 남은 integration의 supersede 거부, (5) stopped/superseded가 update/adopt를 막지 않음, (6) old-baseline 정리 dry-run.
- 공식 spec(`docs/spec/FLOW_SPEC.md`, `GATES_AND_LOOPS.md`), 배포 복제본(`src/forgeflow/spec/`), 생성 skill 안내의 lifecycle 정의 일치 반영.

## 비목표

- repository 전체 active workflow 1개 제한.
- 무관한 staged/unstaged/untracked 변경의 자동 commit/stash/reset/delete.
- plan 변경의 일률 재승인·전체 회귀 강제, 오래된 기록 자동 취소/완료, 이름 기반 우회 방지 규칙.
