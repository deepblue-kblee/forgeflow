# ADR-005: 경량 workflow와 실행 소유권

- 상태: Accepted for v0.1.25, 2026-11-02
- 대체 범위: ADR-001/002 및 과거 strict 기본 운영 가정. 원문 역사·완료 evidence는 보존합니다.

## 결정

ForgeFlow는 요구사항·계획·구현·프로젝트 검증·허용된 통합·task-owned 정리를 조정합니다. 기본 흐름은 단일 agreement/state와 두 진행 조건을 사용합니다. 구현 전 scope/acceptance/plan/checks, 통합 전 검증 통과·operation authority를 확보합니다. 기본 QA/candidate seal·다중 서명·global clean worktree 요구는 제거합니다.

Spec Kit은 계획 도구, project commands는 검증, Git/owning host는 repository operations를 실행합니다. Source/target/owner/route/permissions를 한 번 기록합니다. Host checkout에 중복 branch를 만들지 않고 ready/integrated/cleaned 및 위임 범위 완료를 구분합니다. 통합 성공·정리 실패는 정리부터 재개합니다.

Active 작업은 executable content-addressed runtime/spec/template baseline을 유지합니다. Global current와 same-version replacement가 조용히 이를 바꾸지 못합니다. Adoption은 이유·영향 검토를 기록합니다. Setup/update는 user config/constitution/hooks/evidence를 보존하며 날짜 기준 폐기 정책을 사용하지 않습니다.

## 이전 ADR의 적용 범위

ADR-001의 모든 Git SHA/ref 관찰 전면 금지를 한정합니다. 일반 Git identity는 실행 사실로 기록할 수 있고 content 변화로 검증 freshness를 판단할 수 있습니다. 기존 strict 패키지는 git-sha 또는 sha-free를 명시적으로 유지할 수 있습니다. Default는 QA-SHA/Candidate-SHA/prose seal·global clean ceremony·mandatory package seal을 사용하지 않습니다.

ADR-002의 prose-spec hash 결합 제거는 유지합니다. 무해한 문서 변경으로 영향 없는 구현 증거를 다시 열지 않습니다. ADR-003 config 경로 이전은 사용자 값을 보존하며 active policy·과거 자료 덮어쓰기를 허용하지 않습니다. ADR-004 Counter matching은 선택적 baseline review의 구현 계약이며 universal blocker가 아닙니다.

과거 ADR 원문과 완료 seal artifact는 수정하지 않습니다. 현행 상세 계약은 docs/spec/FLOW_SPEC.md, GATES_AND_LOOPS.md, DISTRIBUTION_SPEC.md가 소유합니다. 배포 복제본은 편집 원본에서 생성합니다.
