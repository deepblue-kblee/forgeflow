# Next Actions & Session Handover

## 완료된 과업 (Completed Tasks)

1. **마크다운 문서 전수 점검 및 최신화 완료 (v0.1.0)**:
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

8. **과거 유산 및 규격 불일치 전수 청산 (v0.1.6)**:
   - **원자적 루프 정의 현대화**: 자가 치유(Loop 2) 루프마다 `git commit (새 SHA 발행)`을 강제하던 조항을 제거하고, 루프 중에는 로컬 수정-테스트를 반복하며 모든 테스트가 100% 통과된 최종 시점에 단일 원자적 커밋 1개를 생성하도록 단일화.
   - **Spec SHA-256 해시 바인딩 잔재 완전 제거**: `FLOW_SPEC.md` 스키마 및 `GATES_AND_LOOPS.md`, `README.md`에 남아있던 해시 바인딩 및 해시 재바인딩 설명 영구 삭제.
   - **거버넌스 용어 및 Stage 표기 단일화**: 모호한 '사전 심사' 표현을 'Gate 1: 명세 승인 (Spec Sign-Off)'으로 완전 통일하고, 구현 단계를 'Stage 3'으로 일치화.
   - **배포 사양 및 버전 관리 정비**: `DISTRIBUTION_SPEC.md`에 전역 `upgrade`와 로컬 `update`, 스마트 파사드 `/update-forgeflow`의 명확한 역할 분리 반영. 과거 버전 번호(v0.22/v0.23 등)를 v0.1.x 표준으로 청산하고 `CHANGELOG.md` 릴리즈 이력 완비.
   - **테스트 및 거버넌스 무결성**: 264개 단위 테스트 100% 통과, 6개 릴리즈 전수 하네스 감사 `forgeflow check --all --strict` 🟢 ALL PASSED, `tasks/completed/v0.1.6-cleanup-legacy-spec-and-sha/` 패키지 밀봉 완료.

9. **Spec Kit 주입 규범 및 훅 통합 공식 사양서 완비**:
   - `docs/spec/SPECKIT_HOOKS_AND_NORMS.md`: Spec Kit 3대 거버넌스 주입 메커니즘, 전체 훅 라이프사이클 및 커밋 매핑, 거시 훅(Macro Hook) vs 미시 체크포인트(Micro Checkpoint) 역할 분담, 피쳐 브랜치 수명주기, 5대 헌법 조항 전문을 단독 문서로 완비.
   - `.specify/templates/commands/implement.md` 및 `src/forgeflow/scaffold.py`: 개별 태스크 체크포인트 커밋 및 안전 롤백 지침 반영 완료.

---

10. **레거시 템플릿 정화, 사양서 발견성 및 비파괴적 부팅 앵커 완비 (v0.1.7)**:
    - **레거시 템플릿 5종 영구 삭제**: `src/forgeflow/templates/` 최상위에서 2026-10-20 이전 산출물(`PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`)을 완전히 삭제하여 Date-Based Amnesia 정책을 철저히 관철. `scaffold.py`에 `LEGACY_TEMPLATES` 분리 및 인라인 fallback을 제공하여 기존 테스트 하위 호환성을 100% 보존.
    - **인스톨러 정화 로직 탑재 (`install.sh`)**: 패키지 배포 시 대상 라이브러리 디렉토리(`$PKG_LIB_DIR/templates/`)에서 구버전 레거시 파일들을 자동으로 정리(Purge)하도록 개선.
    - **사양서 발견성(Spec Discovery) 아키텍처 완비**: `.specify/memory/constitution.md` 및 `scaffold.py` 내장 헌법에 7대 공식 사양서 단일 진실 공급원(SSOT) 참조 경로를 주입하고 `setup-forgeflow`, `update-forgeflow` 스킬 문서 동기화.
    - **비파괴적 세션 진입점 앵커 주입 (`bind_boot_anchor`)**: 고유 식별 마커(`<!-- forgeflow:boot-anchor:start -->` / `end`)를 통해 `AGENTS.md` / `CLAUDE.md`의 기존 사용자 고유 지침을 100% 보존하면서 부팅 시퀀스 앵커를 인플레이스 갱신 및 안전하게 주입/해제하는 엔진 구현 (`tests/test_boot_anchor.py` 7개 테스트 100% Pass).
    - **`forgeflow doc` (및 호환 별칭 `spec`) CLI 구현**: 터미널에서 7대 공식 사양서를 손쉽게 열람할 수 있는 목록 조회(`doc list`) 및 개별 사양 출력(`doc show <spec>`) 인터페이스 제공. 기계 가독형 `--json` 및 커스텀 경로 `--path` 완비 (`tests/test_doc_cli.py` 11개 테스트 100% Pass).
    - **테스트 및 거버넌스 무결성**: 총 282개 테스트 100% Pass, 7개 릴리즈 전수 하네스 감사 `forgeflow check --all --strict` 🟢 ALL PASSED 달성, `tasks/completed/v0.1.7-purge-legacy-templates-and-spec-discovery/` 밀봉 완료.

---

11. **부팅 앵커 기존 주석 삭제 및 파일 맨 마지막 추가 개선 (v0.1.8)**:
    - **기존 주석 삭제 및 맨 마지막 추가(Append/Relocate) 엔진 구현**: `AGENTS.md` / `CLAUDE.md` 파일에 ForgeFlow 부팅 앵커 주입 시, 기존 상단/중간에 위치하던 주석 마커 블록을 정규식 기반으로 완전히 삭제하고 파일 맨 마지막(하단)으로 이동하여 안전하게 추가하도록 개선 (`bind_boot_anchor`).
    - **프로젝트 고유 컨텍스트 최상위 보존**: 타깃 프로젝트 고유의 메인 타이틀(`# Project Title`) 및 개요를 100% 최상위에 온전히 유지하여 비침습적 거버넌스 바인딩 달성.
    - **멱등성 및 원복 무결성**: 이미 파일 맨 끝에 최신 앵커가 위치하는 경우 디스크 쓰기 없는 멱등성(`unchanged`) 보장 및 `unbind_boot_anchor`의 안전한 원복 검증.
    - **테스트 및 거버넌스 무결성**: 상단/중간 위치 기존 주석 삭제 및 하단 재배치 검증 단위 테스트 2종 추가(총 9개 부팅 앵커 테스트 100% Pass), 전체 284개 단위 테스트 100% Pass, 8개 릴리즈 전수 거버넌스 감사 `forgeflow check --all --strict` 🟢 ALL PASSED 달성, `tasks/completed/v0.1.8-append-boot-anchor/` 패키지 밀봉 완료.

---

## 새 세션에서 바로 이어서 착수할 과업 (Next Actions)

### 🎯 다음 작업 방향
1. **GitHub Issues 모니터링 및 추가 개선 사항 접수**:
   - `forgeflow issue list`를 통한 추가 이슈 확인 및 처리.
2. **도그푸딩 및 원격 동기화**:
   - `git push origin main`을 통해 원격 저장소에 최신 버전 배포.
   - 필요 시 타깃 프로젝트에서 `/update-forgeflow`를 실행하여 사양서 발견성과 개선된 하단 부팅 앵커가 정상 반영되는지 검증.
