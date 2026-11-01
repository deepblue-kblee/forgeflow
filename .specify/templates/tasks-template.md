---
description: 의존 순서에 따른 구현 태스크
---

# Tasks: [FEATURE]

입력: [spec/plan 링크]. __SPECKIT_COMMAND_TASKS__로 작성합니다.

## 구현

- [ ] T001 [관찰 가능한 완료 조건 재현/확립; 정확한 파일]
- [ ] T002 [Scoped 동작 구현; 의존 관계]
- [ ] T003 [필요한 회귀/경계 테스트]

예시를 실제 task로 교체합니다. [P]는 독립 파일 소유권·의존 없음 표시이며 subagent 실행이나 무관한 파일 변경 권한이 아닙니다.

## 검증·마무리

- [ ] Project/task checks 실행·실제 결과 확인
- [ ] 영향받는 연결/entrypoint 확인
- [ ] 기록한 owner로 허용된 integration/cleanup 진행
- [ ] 관찰된 endpoint·잔여 blocker 보고

Project 필수 검사를 유지합니다. 동작을 검증하며 구현을 그대로 복사한 테스트나 불필요한 cosmetic output 단언을 피합니다. Pass를 얻으려고 acceptance를 낮추지 않습니다.

Checkbox는 관찰된 구현 진행이며 Git merge/cleanup을 증명하지 않습니다. Checkbox마다 commit을 요구하지 않습니다. __SPECKIT_COMMAND_IMPLEMENT__는 agreement의 scope/권한을 지키며 자동 branch 생성/reset/stash를 하지 않습니다.
