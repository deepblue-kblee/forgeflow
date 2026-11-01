# 엔지니어링 판단 원칙

ForgeFlow는 한 번 위임한 변경이 허용된 완료 지점에 도달하도록 조정합니다. 구현·검증·통합·정리 중 실제 위임된 범위를 끝까지 확인합니다. 계획은 Spec Kit, 검증은 프로젝트 도구, repository operations는 Git/owning host가 수행합니다.

## 판단 기준

실제 요구를 만족하는 가장 작은 장치를 사용합니다. 작은 수정에는 짧은 계획과 의미 있는 검증을, 고위험 변경에는 필요한 독립 심사·승인을 적용합니다. 프로젝트 보호 규칙을 지키며 이미 확보한 권한을 반복 확인하지 않습니다.

각 계약에는 하나의 소유 문서를 두고 실행 사실에는 단일 task state를 사용합니다. 동일 승인·장부·보고를 중복 작성하지 않습니다. 공식 spec은 한 편집 원본과 기계적인 배포 복제본으로 관리합니다.

정상성은 변경 동작·consumer 연결·기대 entrypoint의 실제 실행으로 판단합니다. Cosmetic 출력·report 변경으로 무관한 구현 loop를 열지 않습니다. 실행 성공을 꾸미거나 package seal을 Git merge로 보고하지 않습니다.

Core는 Python 3.10+ 표준 라이브러리를 유지합니다. Spec Kit·project linter·Graphify는 위임 도구이며 숨은 필수 core dependency가 아닙니다.

## 코드 탐색

넓은 architecture 질문에는 사용 가능한 symbol/dependency 지도로 연결을 좁힙니다. 정확한 파일·심볼 질문에는 targeted rg와 focused read를 사용합니다. Graphify가 없다는 이유만으로 가능한 개발 작업을 막지 않습니다.

## 완료와 한계

일반적인 복구 가능 실패는 수정·검증하며 진행합니다. 권한·필수 외부 승인·필수 capability·반복 무진전은 특정 단계를 막을 수 있습니다. 성공한 단계는 유지하고 다음 구체적 행동을 알립니다. 자동 복구로 사용자 변경을 폐기하지 않습니다.

[FLOW_SPEC.md](FLOW_SPEC.md)와 [GATES_AND_LOOPS.md](GATES_AND_LOOPS.md)가 실행 규칙을 소유합니다. Session checkpoint는 docs/session-state/next-actions.md입니다. 과거 완료 package는 증거이며 행동 지침이 아닙니다.
