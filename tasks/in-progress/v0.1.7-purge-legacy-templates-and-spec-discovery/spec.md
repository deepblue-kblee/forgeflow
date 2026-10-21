# Specification: Purge Legacy Templates and Enable Spec Discovery

- **Release ID**: `v0.1.7-purge-legacy-templates-and-spec-discovery`
- **Created Date**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core Templates, CLI Surface & Installer Lifecycle)**

---

## 1. 개요 및 목적 (Overview & Purpose)

Spec Kit 하이브리드 표준 아키텍처가 확립되었음에도 불구하고, 소스 및 배포판에 2026-10-20 이전 v0.22 시절의 레거시 템플릿(`PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`)이 잔존하고 있다. 또한 타깃 프로젝트에서 작업하는 AI 에이전트가 프레임워크의 상세 사양서(`FLOW_SPEC.md` 등)를 찾아보고 참조할 수 있는 경로와 조회 인터페이스가 부재하다.

본 릴리즈는:
1. 소스 및 배포판(`install.sh`, `forgeflow upgrade`)에서 불필요한 레거시 템플릿 5종을 영구 삭제 및 자동 정화한다.
2. 타깃 프로젝트 헌법([`constitution.md`](file:///.specify/memory/constitution.md))과 스킬 지침에 전역 사양서 단일 진실 공급원(SSOT) 참조 경로를 명시한다.
3. 사용자와 AI 에이전트가 언제든 터미널에서 사양서를 검색하고 열람할 수 있는 `forgeflow doc` CLI 서브커맨드를 정식 제공한다.

---

## 2. 세부 요구사항 (Detailed Requirements)

1. **레거시 템플릿 영구 삭제**:
   - `src/forgeflow/templates/` 최상위의 `PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md` 파일 영구 삭제.
   - `scaffold.py`에서 삭제된 파일들에 대한 의존성 정리 (필요 시 Spec Kit 하이브리드 전용으로 통일).
2. **배포판 정화 로직 (`install.sh`)**:
   - `install.sh` 실행 시, 기존 배포 패키지 디렉토리에 남아있을 수 있는 레거시 템플릿 파일들을 자동으로 삭제(Purge)하는 로직 탑재.
3. **사양서 참조 경로 주입 (Spec Discovery for Agents)**:
   - `.specify/memory/constitution.md`, `src/forgeflow/scaffold.py`, `scripts/install-skills.sh`, `~/.agents/skills/`에 전역 사양서 디렉토리(`~/.local/forgeflow/current/lib/forgeflow/templates/spec/`) 및 핵심 문서(7종) 참조 경로 안내 추가.
4. **비파괴적 세션 진입점 앵커 주입 (`AGENTS.md` / `CLAUDE.md`)**:
   - AI 에이전트가 타깃 프로젝트 세션 부팅 시 가장 먼저 읽는 `AGENTS.md` (또는 `CLAUDE.md`)에 마커 태그(`<!-- forgeflow:boot-anchor:start -->` ... `<!-- forgeflow:boot-anchor:end -->`)로 감싼 부팅 시퀀스 앵커를 주입.
   - 멱등성 및 원본 보존 보장: 파일이 이미 존재할 경우 기존 마커 블록만 인플레이스 교체하며, 파일 내 기존 사용자 작성 내용은 1바이트도 훼손하지 않음. 마커가 없으면 안전하게 삽입하고, 다회 실행되어도 중복 주입을 방지.
   - `forgeflow init` 및 `forgeflow update` 시 자동 동기화 적용.
5. **`forgeflow doc` CLI 서브커맨드 구현**:
   - `forgeflow doc` (또는 `forgeflow doc list`): 사용 가능한 공식 사양서 목록 및 파일 경로, 요약 표시.
   - `forgeflow doc <name>` (또는 `forgeflow doc show <name>`): 지정된 사양서의 전체 경로와 마크다운 본문 출력.
   - `--path` 옵션으로 특정 사양 경로 직접 지정 지원.
   - `--json` 옵션으로 기계 가독형 출력 지원.
6. **버전 갱신**:
   - `src/forgeflow/_version.py`를 `0.1.7`로 판올림.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `src/forgeflow/templates/`에서 `PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`가 완전 삭제되고 배포판에도 포함되지 않는다.
- **AC-2**: `install.sh` 실행 시 패키지 디렉토리의 레거시 템플릿 잔재가 자동으로 정리(Purge)된다.
- **AC-3**: `.specify/memory/constitution.md` 및 `src/forgeflow/scaffold.py`에 전역 사양서 참조 경로가 명시된다.
- **AC-4**: `AGENTS.md` / `CLAUDE.md`에 비파괴적 주석 마커 블록(`<!-- forgeflow:boot-anchor:start -->` / `end`) 형태로 앵커가 주입·갱신되며 기존 내용이 훼손되지 않는다.
- **AC-5**: `forgeflow doc` CLI 서브커맨드가 정상 동작하여 `list` 및 개별 사양서(`FLOW_SPEC`, `GATES_AND_LOOPS`, `SPECKIT_HOOKS_AND_NORMS` 등)를 조회할 수 있다.
- **AC-6**: `tests/test_doc_cli.py` 및 앵커 멱등성 단위 테스트가 작성되고 전체 테스트 스위트 100% 통과 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
- **AC-7**: `src/forgeflow/_version.py` 버전이 `0.1.7`로 승격된다.
