# ForgeFlow 변경 이력

## [0.2.3] - 2026-11-10

### Added
- checkout별 단일 active writer 가드레일: 같은 checkout에 구현·Git 작업을 소유하는 active workflow가 있으면 다른 ID의 `workflow start`를 상태 파일 생성 전에 차단하고, 재개/amend/대체/별도 worktree 경로를 안내.
- `workflow supersede --agreement`: 후속 workflow 생성과 predecessor 연결을 단일 lock에서 원자적으로 수행. 재시도 시 기존 후속을 재사용.
- `workflow stop`/`supersede`가 미커밋 변경·남은 cleanup을 `obligations`로 보존하고 `list`/`status`에 표시.

### Changed
- 단일 lifecycle 판정 `_is_writer`를 도입해 `workflow list`, `update`/`init`의 active-work 판정, `adopt`가 같은 정의를 공유.
- `workflow amend`와 `workflow stop`은 완료 기록을 재오픈하지 않음.
- `workflow supersede`는 cleanup이 남은 통합 기록을 대체로 숨길 수 없음.

### Fixed
- stopped/superseded 기록이 `forgeflow update`/`init`/`adopt`를 잘못 차단하던 lifecycle 판정 불일치.
- `.forgeflow/workflows/` runtime state를 `.gitignore`에 추가.

### Verification
- 246 tests OK, sync-distribution match.

## [0.2.2] - 2026-11-07

### Added
- `workflow amend`: 진행 중 agreement의 scope/plan/checks/acceptance를 새 workflow 없이 보완. operation 권한·repository/target은 불변이며, 보완 시 기존 verification을 폐기.
- `workflow list`: active workflow 기본 조회와 `--all` 전체 이력(active/completed/stopped/superseded).
- `workflow supersede`: 대체된 workflow에 후속 ID와 이유를 기록하고 finalize를 차단.
- 일반 `workflow stop`/`resume`: design checkpoint와 별개로 통합 전 작업을 보류·재개.
- `workflow status`/`check`의 `interpretation`: 검증 기록, 관찰된 Git 결과, 선언/증거 연결 acceptance, 이력 증거를 구분.
- blocker별 `cause`, `minimal_action`, `state_command`, `mutation_command`, `requires_user` 안내.

### Changed
- ForgeFlow workflow는 사용자의 명시 요청 또는 실제 `forgeflow` skill 사용 시에만 활성화. 단순 commit/push 요청에 workflow·메타데이터 commit을 만들지 않음.
- workflow 단위 선택, 재개·수정·분리·대체 선택표, `planned`/`ready`/`initial_head` 해석 주의를 공식 spec·README·AGENTS·생성 skill에 반영.
- 외부에서 이미 수행한 commit/push를 관찰 가능한 Git 증거로 연결하는 경로를 문서화하고 검증.

### Verification
- clean init/제거된 legacy surface 계약 테스트와 CLI-level HITL JSON state 검증 추가.
- Python 3.10/3.12 import·version·HITL smoke 검증.

## [0.2.1] - 2026-11-03

### Fixed
- Installer now accepts a symlinked `~/.agents/skills` root by resolving it to the real directory before publication, while still rejecting symlinks inside individual skill directories/files.

## [0.2.0] - 2026-11-03

### Lean workflow with optional design review

### Changed
- 기본 flow를 단일 agreement/state 기반 lean workflow로 유지하고, 디자인 종료 지점에 선택적 HITL checkpoint를 추가. `workflow start --hitl design`에서만 멈추며 기본은 auto 진행.
- `workflow continue`, `workflow revise`, `workflow stop`으로 설계 검토 결정을 state에 기록.
- `speckit-implement`를 `speckit-tasks`와 짝을 이루는 구현 실행 단계로 명시.
- `tasks/`, `docs/releases/`, strict lifecycle/audit CLI, legacy migration code를 active surface에서 제거. 과거 자료는 `archive/pre-0.2.0` tag에 보존.
- `forgeflow init`은 `tasks/`를 만들지 않고 `.forgeflow/workflows`와 runtime/spec baseline만 구성.
- `forgeflow update`는 현재 0.2.x project만 갱신하며, legacy layout은 `forgeflow-migrate` 안내와 함께 거절.
- 0.1.x user project 정리는 별도 `archive/forgeflow-migrate` branch의 migration tool이 담당.

### Compatibility
- 0.1.x project는 자동 변환되지 않음. `forgeflow-migrate`로 `tasks/`, old strict 자산, legacy docs를 archive tag에 보존한 뒤 제거.
- 완료된 과거 evidence는 archive tag와 Git history에서만 확인.

## [0.1.x] - 2026-10-20 ~ 2026-11-02

Gate 기반 strict lifecycle, Spec Kit 하이브리드 거버넌스, QA-SHA/seal, package 기반 배포를 제공하던 이전 세대. 0.2.0에서 lean/HITL flow로 대체되었으며 active code와 문서에서는 제거되었다.
