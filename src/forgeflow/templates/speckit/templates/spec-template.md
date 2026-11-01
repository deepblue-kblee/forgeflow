# 기능 명세: [FEATURE]

입력: [사용자 요구사항]. 기존 source/owner: [agreement 참조].

## 범위·관찰 가능한 완료 조건

- In scope: [경로/동작]
- Out of scope: [중요 경계]
- Acceptance: [관찰 가능한 정상·실패 결과]

## 사용자 시나리오

1. Given [상태], when [행동], then [결과].
2. Given [실패/경계], when [행동], then [기대 결과].

## 요구사항·결정

- [기능 요구사항]
- [관련 compatibility/security/data 제약]
- [중대한 사용자 미결 사항만 기록; 일반 기술 선택의 반복 질문 금지]

## 검증·권한

필수 checks·source/target·owner·permissions는 workflow agreement/state를 참조합니다. Project workflow.checks를 제거할 수 없으며 기존 host checkout에 branch를 중복 생성하지 않습니다.

작은 task는 짧은 계획을 사용합니다. 필요한 section만 추가하며 기본 다중 서명 package/prose hash를 요구하지 않습니다.
