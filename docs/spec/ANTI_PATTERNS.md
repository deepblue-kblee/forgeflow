# 설계 경계

| 피할 패턴 | 적용할 원칙 | 소유 계약 |
| --- | --- | --- |
| 모든 작업에 과거 Gate/seal 강제 | 선택적 design checkpoint와 project checks | [Flow](FLOW_SPEC.md) |
| Readiness를 merge/cleanup으로 보고 | ready/integrated/cleaned 구분 | [Flow](FLOW_SPEC.md) |
| Git/worktree 중복 소유·일괄 정리 | owner/source/target/permissions 기록, task-owned 대상만 정리 | [Flow](FLOW_SPEC.md) |
| 무관한 변경의 자동 stage/reset/stash | 사용자 변경 보존, 영향 operation만 차단 | [검증](GATES_AND_LOOPS.md) |
| Universal raw Warning 0 강제 | 선언된 checks와 선택적 review | [검증](GATES_AND_LOOPS.md) |
| installer exit 0·version 문자열만으로 성공 | 실제 package/entrypoint/spec/skills 검증 | [배포](DISTRIBUTION_SPEC.md) |
| Current 조용한 변경·날짜 기준 삭제 | 실행 baseline 고정·명시적 adoption·사용자 파일 보존 | [배포](DISTRIBUTION_SPEC.md) |
| 과거 strict code를 core에 계속 유지 | archive tag/branch로 보존하고 active surface에서 제거 | [배포](DISTRIBUTION_SPEC.md) |
| 무진전 반복 조사 | 증거·진행 기록·stop rule | [검증](GATES_AND_LOOPS.md) |
| Core의 third-party runtime dependency | Python 3.10+ 표준 라이브러리 | [판단 원칙](PHILOSOPHY_AND_COMPASS.md) |
