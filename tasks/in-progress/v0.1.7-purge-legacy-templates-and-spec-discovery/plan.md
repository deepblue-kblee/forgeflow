# Architecture & Implementation Plan: Purge Legacy Templates and Enable Spec Discovery

- **Release ID**: `v0.1.7-purge-legacy-templates-and-spec-discovery`
- **Target Version**: `v0.1.7`
- **Status**: READY FOR TASK BREAKDOWN

---

## 1. 아키텍처 원칙 및 변경 설계 (Architecture Design)

### 1.1 레거시 템플릿 영구 삭제
- 대상 파일:
  - `src/forgeflow/templates/PRD.md`
  - `src/forgeflow/templates/DESIGN.md`
  - `src/forgeflow/templates/ROADMAP.md`
  - `src/forgeflow/templates/GOVERNANCE.md`
  - `src/forgeflow/templates/RELEASE_NOTES.md`
- 보존 파일:
  - `src/forgeflow/templates/spec/**` (7대 공식 사양서)
  - `src/forgeflow/templates/speckit/**` (Spec Kit 번들 스크립트 6종 및 템플릿 4종)
  - `src/forgeflow/templates/QA_SIGNOFF.md` (Gate 2 템플릿)
  - `src/forgeflow/templates/RELEASE_SIGNOFF.md` (Gate 3 템플릿)
  - `src/forgeflow/templates/COMPLETION_REPORT.md` (완료 보고 템플릿)

### 1.2 `scaffold.py` 및 테스트 정비
- `scaffold.py`의 `BUNDLE_FILES` 및 `create_release_scaffold`에서 삭제된 파일 참조 제거.
- `tests/test_scaffold.py`에서 레거시 템플릿 검증 항목을 현대화된 템플릿 검증으로 갱신.

### 1.3 `install.sh` 내 배포판 레거시 정화 로직
- `install.sh` 실행 시, `$PKG_LIB_DIR/templates/` 및 전역 템플릿 디렉토리에서 과거에 복사되었던 레거시 파일들(`PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`)을 강제 삭제(`rm -f`)하는 정화 스텝 추가.

### 1.4 사양서 참조 경로 주입 (헌법 및 스킬)
- [`.specify/memory/constitution.md`](file:///.specify/memory/constitution.md) 및 `src/forgeflow/scaffold.py` 내장 헌법:
  하단에 `## 프레임워크 공식 사양서 참조 경로 (Framework Specifications)` 섹션을 추가하여 `~/.local/forgeflow/current/lib/forgeflow/templates/spec/` 경로와 7대 사양서 목록 명시.
- `scripts/install-skills.sh`, `~/.agents/skills/setup-forgeflow/SKILL.md`, `~/.agents/skills/update-forgeflow/SKILL.md`에 사양서 참조 안내 추가.

### 1.5 비파괴적 세션 진입점 앵커 주입 (`AGENTS.md` / `CLAUDE.md`)
- `scaffold.py`에 `bind_boot_anchor(root: Path, target_names: Sequence[str])` 로직 구현:
  - 마커 태그 정의: `<!-- forgeflow:boot-anchor:start -->` 및 `<!-- forgeflow:boot-anchor:end -->`
  - 앵커 본문: 헌법(`.specify/memory/constitution.md`), 7대 사양서(`forgeflow doc list`), Gate 1 준수, Loop 2/3 행동 규범을 안내하는 간결한 마크다운 블록.
  - 멱등성 및 원본 보존:
    - 대상 파일(`AGENTS.md`, `CLAUDE.md`)이 이미 존재할 경우:
      - 기존 마커 블록이 있으면 해당 블록 내부만 치환 (인플레이스 업데이트).
      - 마커 블록이 없으면 파일 상단(헤더 직후)에 마커 블록을 안전하게 삽입하고 기존 텍스트는 100% 보존.
    - 파일이 존재하지 않을 경우: 새 파일 생성 후 마커 블록 작성.
  - `forgeflow init` 및 `forgeflow update` 실행 파이프라인에 연결하여 자동 동기화.

### 1.6 `forgeflow doc` CLI 서브커맨드 구현
- `src/forgeflow/cli.py`:
  - `doc` 서브커맨드 추가:
    - 인자 `name` (optional): 조회할 사양서 이름 (예: `FLOW_SPEC`, `GATES_AND_LOOPS`, `all` 등).
    - `--list` 플래그: 사용 가능한 사양서 목록 출력.
    - `--json` 플래그: 기계 가독형 JSON 출력.
  - 핸들러 `handle_doc(args)`:
    - 사양서 디렉토리 탐색 우선순위:
      1) 로컬 개발 저장소의 `docs/spec/` (존재할 경우)
      2) 설치된 패키지 런타임의 `templates/spec/`
      3) 전역 배포본 `~/.local/forgeflow/current/lib/forgeflow/templates/spec/`
    - 사양서 목록 또는 본문을 서식화하여 출력.

### 1.7 테스트 및 버전 승격
- `tests/test_doc_cli.py` 및 `tests/test_boot_anchor.py`(앵커 멱등성 및 원본 보존 검증) 작성 및 100% 검증.
- `_version.py`를 `0.1.7`로 판올림.
