# Next Actions

## 완료된 과업 (Completed Tasks)

1. **마크다운 문서 전수 점검 및 최신화 완료**:
   - `AGENTS.md`: 옛 산출물(`PRD.md`, `DESIGN.md`, `RTM`) 영구 삭제 및 최신 Spec Kit 하이브리드 아키텍처(`spec.md`, `plan.md`, `tasks.md`, `GATE1_REVIEW.md`, `QA_SIGNOFF.md`, `RELEASE_SIGNOFF.md`) 반영.
   - `AGENTS.md` & `SKILL.md`: 2026-10-20(v0.1.0 릴리즈일) 이전 과거 버전/흔적 강제 폐기 규범(Date-Based Amnesia Policy) 주입.
   - `README.md`, 세션 상태 문서 최신화 완료.

2. **GitHub Issue #1 완결 및 배포 (v0.1.1)**:
   - Spec Kit 필수 bash 스크립트 6종 및 마크다운 템플릿 4종 프레임워크 내부 번들링.
   - 하이브리드 스캐폴딩(`scaffold_speckit_hybrid`) 시 스크립트 자동 생성 및 `0o755` 실행 권한 부여.
   - 거버넌스 감사 엔진(`validator.py`, `harness.py`) 하이브리드 산출물 정식 인식 지원.
   - 진단 엔진(`diagnostics.py` / `doctor`)에 Spec Kit 전제조건 및 레거시 설정 감지 룰 탑재.
   - 실전 Spec Kit 하이브리드 워크플로우(Stage 1 ~ Stage 5) 도그푸딩 완주 및 릴리즈 패키지 밀봉(`tasks/completed/v0.1.1-fix-speckit-prerequisites/`).
   - 계정 로컬 환경에 `ForgeFlow v0.1.1` 배포 및 GitHub Issue #1 종결 완료.

## 다음 할 일 (Next Tasks)

1. **외부 타깃 프로젝트 실전 적용 및 추가 도그푸딩**:
   - 신규 외부 프로젝트에서 `curl -sSL https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh | bash` 및 `/setup-forgeflow` 실행 테스트.
   - `/speckit.specify`부터 `/speckit.implement`까지의 외부 프로젝트 사용자 경험 검증.
