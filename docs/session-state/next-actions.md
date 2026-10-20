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

6. **레거시 `update` 명령어 및 구버전 카탈로그 완전 폐기 (v0.1.4)**:
   - **`forgeflow update` 서브커맨드 영구 제거**: 2026-10-20 이전 v0.4.4~v0.22.0 시절의 구시대 잔재였던 `update` 명령어를 CLI 파서 및 디스패치에서 영구 삭제.
   - **레거시 모듈 및 자산 청산**: `update.py`, `bundle_catalog.py`, `catalog_oracles/`, `tests/test_update.py` 등 약 660줄의 레거시 코드를 완전 삭제하여 Date-Based Amnesia Policy 완벽 관철.
   - **단일 표준 확립**: 전역 런타임 업그레이드는 `forgeflow upgrade`, 로컬 프로젝트 거버넌스 마이그레이션은 `/update-forgeflow` 스킬로 일원화.
   - **테스트 무결성**: 263개 테스트 100% Pass 및 `forgeflow check --all --strict` 4개 릴리즈 전수 🟢 ALL PASSED.

7. **`forgeflow update` 로컬 거버넌스 동기화 명령 재정의 및 스킬 연동 (v0.1.5)**:
   - **`forgeflow update` CLI 정식 도입**: 로컬 리포지토리의 거버넌스 사양(`.forgeflow.json`, `.specify/scripts/bash/`, 템플릿, 헌법, 훅)을 최신 규격으로 동기화하고 `tasks/` 작업 패키지 데이터를 100% 안전하게 보존.
   - **스마트 파사드 `/update-forgeflow` 간결화**: 복잡한 파일 복사 지침 대신 전역 `forgeflow upgrade` ➔ 로컬 `forgeflow update`를 순차 호출하도록 DRY 원칙 기반 캡슐화 완성.
   - **대칭 구조 확립**:
     - 전역 런타임/스킬 판올림: `forgeflow upgrade`
     - 현재 작업 repo 사양 갱신: `forgeflow update`
     - 에이전트 통합 원스톱 파사드: `/update-forgeflow` 스킬
   - **테스트 및 거버넌스 무결성**: 신규 단위 테스트 추가 (총 264개 테스트 100% Pass), 5개 릴리즈 전수 하네스 감사 `forgeflow check --all --strict` 🟢 ALL PASSED, `tasks/completed/v0.1.5-redefine-update-command-and-facade/` 패키지 밀봉 완료.

## 다음 할 일 (Next Tasks)

1. **Git 원격 반영 (Push)**:
   - `git push origin main`을 실행하여 최신 릴리즈(v0.1.5)를 GitHub 원격에 반영.
2. **전역 런타임 최신화 (최초 1회 install.sh)**:
   - 원격 푸시 후 `bash install.sh`를 실행하여 로컬 OS 전역 CLI(`~/.local/bin/forgeflow`)를 `v0.1.5`로 승격.
3. **외부 타깃 프로젝트 실전 적용 및 검증**:
   - 다중 저장소(Repo A, Repo B 등)에서 `forgeflow update` 또는 `/update-forgeflow` 스킬을 실행하여 전역 업그레이드와 로컬 사양 동기화의 유기적 동작 검증.
