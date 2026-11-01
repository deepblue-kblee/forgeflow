# 🧭 ForgeFlow Official Specifications Index & Router

이 문서는 ForgeFlow 프레임워크의 공식 사양서 색인 및 상황별 라우터이다.
모든 문서를 처음부터 전부 읽지 않는다. 현재 진행 중인 작업 단계에 지정된 사양서만 선별 참조한다.

---

## 🚦 작업 단계별 사양서 라우팅 테이블

| 작업 단계 / 상황 | 필수 사양서 | 핵심 확인 및 준수 사항 |
| :--- | :--- | :--- |
| **새 기능 기획 & 명세 작성**<br>(Stage 1: `/speckit.specify`, `clarify`) | [`ANTI_PATTERNS.md`](file://ANTI_PATTERNS.md)<br>[`FLOW_SPEC.md`](file://FLOW_SPEC.md) | - Git SHA/커밋 범위 결합 및 해시 바인딩 금지<br>- `spec.md` 인수 조건(Acceptance Criteria) 임의 축소·삭제 금지 |
| **Gate 1 사전 명세 심사**<br>(Gate 1: Spec Review) | [`GATES_AND_LOOPS.md`](file://GATES_AND_LOOPS.md) | - Tier 1/2/3 리스크 등급 판정 및 사전 승인 획득<br>- `GATE1_REVIEW.md` 공식 `APPROVED` 전 코드 작성/수정 절대 금지 |
| **기술 설계 & 태스크 분해**<br>(Stage 2: `/speckit.plan`, `tasks`) | [`SPECKIT_HOOKS_AND_NORMS.md`](file://SPECKIT_HOOKS_AND_NORMS.md)<br>[`REFACTORING_GUIDE.md`](file://REFACTORING_GUIDE.md) | - `plan.md` 아키텍처 설계 및 `tasks.md` 원자적 TDD 체크리스트 분해<br>- 모듈 간 결합도 제어 및 Zero-Dependency 원칙 유지 |
| **격리 구현 & 자가 치유**<br>(Stage 3: `/speckit.implement`) | [`GATES_AND_LOOPS.md`](file://GATES_AND_LOOPS.md) | - 단순 테스트/린트 실패는 가짜 멈춤(False Stop); Loop 2 자율 치유 완주<br>- 동일 에러 5회 연속 실패 시에만 진짜 멈춤(True Stop) 에스컬레이션 |
| **QA 품질 검증**<br>(Gate 2: QA Sign-Off) | [`GATES_AND_LOOPS.md`](file://GATES_AND_LOOPS.md) | - 단위/통합 테스트 100% 통과 및 `QA_SIGNOFF.md` 승인 증적 생성<br>- 계획된 변경 경로(planned paths)와 실제 diff 일치 검증 |
| **운영 승격 & 릴리즈 밀봉**<br>(Gate 3: Release Sign-Off) | [`DISTRIBUTION_SPEC.md`](file://DISTRIBUTION_SPEC.md)<br>[`FLOW_SPEC.md`](file://FLOW_SPEC.md) | - `RELEASE_SIGNOFF.md` 작성 후 `tasks/completed/`로 패키지 밀봉<br>- 과거 버전(`packages/`) 직접 참조 금지; 오직 `current`만 사용 |
| **아키텍처 철학 & 경계 판단**<br>(프레임워크 코어 의사결정) | [`PHILOSOPHY_AND_COMPASS.md`](file://PHILOSOPHY_AND_COMPASS.md) | - Zero-Dependency (Python 3.10+ 표준 라이브러리 100%) 준수<br>- 프레임워크 자체 도메인과 사용자 프로젝트 도메인의 완전 분리 |

---

## 📌 사양서 목록 요약

1. [`FLOW_SPEC.md`](file://FLOW_SPEC.md): 5단계 폐루프 수명주기, 3단 칸반 구조, 브랜치 격리 규칙.
2. [`GATES_AND_LOOPS.md`](file://GATES_AND_LOOPS.md): Gate 1/2/3 승인 기준, Loop 1~3, 자율 치유 예산(5회 한도).
3. [`SPECKIT_HOOKS_AND_NORMS.md`](file://SPECKIT_HOOKS_AND_NORMS.md): Spec Kit 3대 주입 메커니즘, 훅 라이프사이클 및 TDD 체크포인트.
4. [`ANTI_PATTERNS.md`](file://ANTI_PATTERNS.md): 금지된 안티패턴(Git SHA 결합, 스펙 해시 바인딩, 임의 스펙 하향 등).
5. [`REFACTORING_GUIDE.md`](file://REFACTORING_GUIDE.md): 모듈 분해, 단일 책임 원칙, 복잡도 제어 가이드라인.
6. [`DISTRIBUTION_SPEC.md`](file://DISTRIBUTION_SPEC.md): `~/.local/share/forgeflow/` 사용자 배포, 버전 관리, 업그레이드 규격.
7. [`PHILOSOPHY_AND_COMPASS.md`](file://PHILOSOPHY_AND_COMPASS.md): 핵심 설계 철학, SSOT 경계 및 에이전트 거버넌스 원칙.
