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

3. **인스톨러(install.sh) 및 update-forgeflow 스킬 동기화 보강**:
   - `install.sh`: 기존 설치 감지 및 동일 버전이라도 소스 파일/스킬을 안전하게 최신화(동기화)하도록 개선 (`exit 0` 조기 종료 제거).
   - `update-forgeflow` 스킬: 리포지토리 갱신 시 `.specify/scripts/bash/` 스크립트 6종 및 템플릿 4종을 최신 파일로 동기화하도록 지침 명시.

4. **GitHub Issue #2 완결 및 배포 (v0.1.2)**:
   - **`spec.md` 해시 바인딩(Spec SHA256) 완전 제거**: 사소한 텍스트/포맷 편집에도 해시가 깨져 Loop 3 무한 루프로 헛돌던 마찰 요인 원천 해소 (`cli.py`, `validator.py`, `scaffold.py`).
   - **Stage와 Gate 개념 완전 분리**: 작업 단계(Stage 1~3)와 승인 관문(Gate 1~3: Spec Sign-Off, QA Sign-Off, Release Sign-Off)의 위치, 주체, 승인 방법을 명확히 단일 진실 공급원(SSOT)으로 정비.
   - **문서 내 미구현 CLI 명령어 정비**: `README.md` 및 사양 문서에서 존재하지 않던 `forgeflow gate1 review`, `forgeflow gate2 signoff` 등을 실제 명령어(`check --stage 2`, `review --strict`, `lifecycle package-review`, `lifecycle seal`)로 전면 교정.
   - **릴리즈 밀봉 및 테스트 무결성**: 269개 테스트 100% Pass 및 `forgeflow check --all --strict` 🟢 ALL PASSED 완료. Issue #2 공식 종결.

5. **`forgeflow upgrade` 및 스마트 파사드 스킬 배포 (v0.1.3)**:
   - **`forgeflow upgrade` CLI 서브커맨드 구현**: `--check`로 무설치 버전 확인, 최신 버전일 시 불필요한 재설치 방지(Idempotency), 원격 `install.sh` 자동 다운로드 및 전역 런타임/스킬 일괄 승격 지원.
   - **`update-forgeflow` 스마트 파사드(Smart Facade) 개편**: 1단계 전역 최신화 점검(`forgeflow upgrade`) ➔ 2단계 현재 프로젝트 거버넌스 사양 갱신을 원스톱으로 연결. 다중 repo(A, B, C)에서 언제든 최신 환경으로 일괄 승격 보장.
   - **테스트 무결성**: 신규 6개 단위 테스트 추가 (총 275개 테스트 100% Pass) 및 `forgeflow check --all --strict` 🟢 ALL PASSED 달성.

## 다음 할 일 (Next Tasks)

1. **Git 원격 반영 (Push)**:
   - 사용자가 원격 `git push origin main`을 진행하여 최신 배포본(v0.1.3)을 GitHub에 반영.
2. **외부 타깃 프로젝트 실전 적용 및 추가 도그푸딩**:
   - 신규/외부 프로젝트에서 `install.sh` 및 `/setup-forgeflow` (또는 `/update-forgeflow`) 실행 테스트.
   - `/speckit.specify`부터 `/speckit.implement`까지의 외부 프로젝트 사용자 경험 검증.
