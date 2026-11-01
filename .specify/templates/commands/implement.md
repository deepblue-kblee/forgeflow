---
description: 합의된 계획을 구현하고 필수 프로젝트 검증을 실행합니다
---

## 구현 전

Active workflow agreement/state의 scope·observable acceptance·plan·checks를 확인합니다. Pinned runtime으로 명시적 task ID의 workflow check를 실행합니다. 의도적으로 선택한 strict package는 해당 compatibility entry check를 따릅니다.

## 구현

필요한 task list를 의존 순서로 진행합니다. 실제 실패를 수정하고 영향 검사를 다시 실행합니다. Acceptance·기존 사용자 변경을 보존하고 반복 무진전 조사는 설정된 budget에서 중단합니다.

Commit은 권한과 task-owned scope를 따릅니다. Host worktree 소유권을 유지하며 추가 branch·자동 reset/stash를 하지 않습니다.

구현 후 project/task checks와 허용된 integration/cleanup까지 연결합니다. Ready/integrated/cleaned를 구분합니다. Lifecycle를 중복 정의하지 않고 docs/spec/FLOW_SPEC.md를 따릅니다.
