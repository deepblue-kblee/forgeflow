# ForgeFlow 저장소 작업 지침

## 목적과 단일 기준

ForgeFlow는 요구사항·계획·구현·검증·허용된 통합·정리를 완료까지 조정합니다. 계획은 Spec Kit, 검증은 project tools, repository operations는 Git/owning host에 위임합니다. Core는 Python 3.10+ 표준 라이브러리만 사용하며 third-party runtime dependency를 추가하지 않습니다.

Session 시작 시 docs/session-state/next-actions.md와 docs/spec/README.md를 읽고 현재 작업의 소유 계약을 참조합니다. docs/spec/가 공식 편집 원본이며 src/forgeflow/spec/는 기계적 배포 복제본입니다. 양쪽 정책을 독립 유지하지 않습니다.

tasks/completed/와 과거 docs/releases/는 불변 evidence이며 현행 행동 규칙이 아닙니다. 필요한 compatibility 맥락만 선별 조회합니다. 날짜만으로 사용자 자료를 삭제하지 않습니다.

## 기본 개발 계약

구현 전 scope·observable acceptance·proportionate plan·필수 checks를 확정합니다. 통합 전 해당 검증 성공과 operation 권한을 확인합니다. 작은 변경에 다중 서명·seal을 요구하지 않습니다. 큰 변경에는 Spec Kit spec/plan/tasks를 활용하며 추가 심사는 실제 위험·프로젝트 요구에 따릅니다.

docs/spec/FLOW_SPEC.md의 workflow CLI/state를 사용합니다. 기본 실행 단일 근거는 .forgeflow/workflows/<id>.json입니다. Project workflow.checks를 task 입력으로 제거할 수 없습니다. 선택적 forgeflow review 임계치를 universal blocker로 삼지 않습니다.

기존 release/task/lifecycle는 명시적 strict compatibility입니다. Package-review/signoff/manifest/seal 순서·binding policy는 docs/spec/GATES_AND_LOOPS.md가 정의합니다. 패키지 완료를 통합 증거 없이 merged로 보고하지 않습니다.

## Repository ownership과 권한

이미 받은 사용자 승인을 재사용합니다. Source·target·owner·integration route·각 permission을 한 번 기록합니다. Readiness 자체는 push/merge/delete/deploy 권한이 아닙니다. Local integration에 PR을 강제하지 않습니다.

Host-owned checkout에 다른 branch/worktree를 중복 생성하지 않습니다. Host cleanup은 소유 도구를 사용합니다. Standalone operation은 task-owned paths/branches만 다룹니다. 무관한 staged/unstaged/untracked 변경을 몰래 commit/stash/reset하지 않으며 자동 destructive rollback을 금지합니다.

Ready/integrated/cleaned와 요청 범위 완료 finalization_complete를 구분합니다. Merge 성공·cleanup 실패 시 정리만 재개합니다. 관찰된 Git/host 결과를 확인한 뒤 성공을 보고합니다.

## 검증·심사

작업 중 focused 검사, 통합 전 필요한 관련 suite를 실행합니다. ForgeFlow runtime 변경은 python3 -m unittest discover -s tests -p "test_*.py"와 영향에 맞는 source-entrypoint/delivery 검사를 사용합니다. Legacy parser/lifecycle에 영향이 있으면 해당 archive audit를 수행합니다.

결함을 숨기려고 테스트를 완화하지 않습니다. 의도적 contract 변경은 의미 있는 테스트로 갱신합니다. 코드·환경·통합 결과의 변화가 있을 때 검증을 반복하고 새/Critical 문제와 기존 무관한 findings를 구분합니다.

Governance control-plane 또는 repository-operation authority 변경에는 독립 Security/Reliability/Maintainability 설계·최종 review를 적용합니다. 실제 findings/results를 한 번 기록합니다. 기존 사용자 scope 승인은 유효하며 반복 전체 승인 loop를 만들지 않습니다. 필요한 설계 심사 완료 전 src 구현을 시작하지 않습니다.

반복 실패·조사에 설정된 no-progress budget(통상 5회)을 적용합니다. 동일 자료/명령의 반복은 전진이 아닙니다. 외부 권한·승인·필수 capability·중대한 사용자 결정이 없으면 해당 단계는 먼저 막힐 수 있습니다. 정확한 실패·다음 행동을 기록하고 통과를 꾸미지 않습니다.

## Runtime·release 유지보수

Active 작업은 content identity와 executable local snapshot을 유지합니다. 재개는 해당 state의 baseline.command를 통한 doc show 또는 baseline.path/spec를 사용하며 여러 task의 기준을 project 기본 spec 링크로 대체하지 않습니다. Global current/same-version replacement가 조용히 규칙을 바꿀 수 없습니다. 새 baseline adoption은 명시적 이유·영향 검토를 기록하며 완료 evidence를 보존합니다.

Runtime/tests/공식 specs/지침/배포를 바꾸는 self-maintenance는 src/forgeflow/_version.py와 spec/VERSION을 일치시킵니다. 현재 0.1.X patch 정책을 유지하고 minor 변경은 별도 합의합니다. Runtime·packaged specs/templates·generator·installer 계약을 일치시킵니다.

응집된 단위로 commit하고 저장소가 요구하는 attribution을 지킵니다. Commit/push/merge는 기존 권한 안에서만 수행합니다. Issue close/comment는 해당 사용자 범위가 필요하며 branch push를 merge로 취급하지 않습니다. 개발에 전역 설치 update를 암묵적으로 포함하지 않습니다.

Handoff 전 docs/session-state/next-actions.md에 관찰된 진행·검증·미완·다음 행동을 갱신합니다. 구현 완료·차단·미착수를 정확히 보고합니다.

<!-- forgeflow:boot-anchor:start -->
## ForgeFlow session 진입점

docs/session-state/next-actions.md, .forgeflow/config.json, docs/spec/README.md를 읽습니다. Active task의 pinned runtime·기존 권한을 재사용하고 현 작업의 소유 계약을 따릅니다. 사용자 지침·과거 evidence를 보존합니다.
<!-- forgeflow:boot-anchor:end -->
