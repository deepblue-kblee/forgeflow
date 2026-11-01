# Refactoring 지침

동작·책임·인터페이스를 이해하기 쉽게 만들기 위해 refactor합니다. 의도적으로 검토한 변경 외에는 요구사항·public contract를 유지합니다. 무관한 기존 warning은 저장소 전면 수정의 근거가 아닙니다.

## 구조

응집된 module과 작고 유용한 interface를 사용합니다. 한 번 쓰는 pass-through나 실제 반복 필요가 없는 추상화를 피합니다. 결합을 줄일 때 책임을 나누며 line count만으로 파편화하지 않습니다. Guard clause로 중첩을 줄이고 실제 공유 개념일 때 parameter object를 사용합니다.

## 선택적 분석

forgeflow review는 file/function 길이·cognitive complexity·nesting·parameter 등의 AST signal을 제공합니다. 명시적으로 선택한 project policy일 때만 blocker가 됩니다. Strict review mode는 [GATES_AND_LOOPS.md](GATES_AND_LOOPS.md)가 정의합니다.

결함을 숨기려고 테스트를 바꾸지 않습니다. 의도적 동작 변경은 새 계약의 정상·실패·경계 테스트를 유지합니다. 작업 중 focused 검증, 통합 전 필요한 관련 suite를 사용합니다.

## Runtime·통합

영향받는 전달 entrypoint와 통합 결과를 확인합니다. Report·receipt·checkbox만 바뀌면 유효한 검증을 재사용합니다. 무관한 dirty 파일을 보존하고 부분 완료는 관찰된 상태부터 재개합니다.

[FLOW_SPEC.md](FLOW_SPEC.md)가 workflow·permission·repository ownership을 소유합니다.
