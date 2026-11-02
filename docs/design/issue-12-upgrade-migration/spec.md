# Issue #12: Legacy upgrade/update migration

## 목표

v0.1.24 이하에서 생성된 project와 설치 상태를 새 lean 배포로 이전하되, 사용자 자산과 historical evidence를 보존하고 실제 실행 결과로 성공을 입증한다.

## 범위

- `forgeflow update --dry-run --json`과 `update --json`의 inventory/plan/apply 계약
- v0.1.24 실제 생성물의 ownership 판정과 lean 전환
- update 결과의 created/updated/removed/preserved/conflict/blocker 보고
- `forgeflow upgrade`의 동일 배포 취득, 실제 installed entrypoint 검증
- installer activation 실패 복구와 retention 순서
- 관련 unit/acceptance test와 공식 spec/CHANGELOG/session state 갱신

## 비범위

- 모든 과거 version의 범용 migration platform
- release server, 서명 기반 배포, third-party runtime dependency
- active strict package를 lean으로 자동 변환
- `tasks/completed/`, `docs/releases/` historical evidence 재작성
- 사용자 global install, project, remote branch를 test 중 변경

## 관찰 가능한 acceptance

1. v0.1.24의 미수정 strict constitution·universal hook·implement override가 update 후 lean 기본 지침으로 남지 않는다.
2. 사용자 수정본, custom config/tasks_dir/checks/owner, 무관한 Git 변경은 byte 단위로 보존되고 conflict로 보고된다.
3. `--dry-run`은 filesystem과 Git index를 변경하지 않는다. 같은 update 재실행은 no-op이다.
4. update JSON은 실제 filesystem 결과와 일치하며 `applied|no-op|blocked|partial|error`를 구분한다.
5. active task가 있으면 write 전에 차단하고 task/baseline/재개 command/next action을 반환한다.
6. installer exit 0만으로 upgrade 성공을 보고하지 않는다. 실제 package metadata/entrypoint/spec/skills를 확인한다.
7. 설치가 없거나 version/target 불일치면 non-success와 관찰 상태를 반환한다.
8. activation 실패 시 이전 current/bin과 skills를 복구하고 retention을 실행하지 않는다.

## 지원 legacy 기준

- 판정 기준 배포: v0.1.24 (`2a5de5bb5be8c8cabc65b298d031f6cf6545ece0`)
- manifest 없는 project는 알려진 v0.1.24 생성물의 exact content/hash로만 framework-owned를 판정한다.
- 알 수 없는 bytes는 `user-modified-or-unknown`으로 보존하며 자동 덮어쓰기/삭제하지 않는다.
