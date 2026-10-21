# Specification: Append Boot Anchor to Root Guides

- **Release ID**: `v0.1.8-append-boot-anchor`
- **Created Date**: 2026-10-21
- **Risk Tier**: **Tier 1 (Minor / Fast-track - Local Scaffolding Improvement)**

---

## 1. 개요 및 목적 (Overview & Purpose)

현재 `TemplateScaffolder.bind_boot_anchor`는 `AGENTS.md` 또는 `CLAUDE.md` 파일에 ForgeFlow 부팅 앵커 마커(`<!-- forgeflow:boot-anchor:start -->` ~ `<!-- forgeflow:boot-anchor:end -->`)를 주입할 때 문서 최상단에 주입(Prepend)하거나 중간에 인플레이스로 유지하고 있었다.
이는 프로젝트 고유의 메인 제목(`# Project Title`) 및 개요보다 외부 도구 안내 문구가 먼저 노출되어 프로젝트 문서 계층 구조를 해치고 침습적으로 느껴지는 문제가 있다.

본 릴리즈는:
1. `AGENTS.md` 및 `CLAUDE.md`에 부팅 앵커를 주입할 때, 기존에 상단이나 중간 등에 이미 작성되어 있던 주석 블록을 완전히 삭제(제거)하고 파일의 맨 마지막(하단)에 안전하게 추가(Append/Relocate)하도록 개선한다.
2. 기존 문서의 원본 내용과 개행을 100% 보존하면서 말미에 앵커 블록을 덧붙여 프로젝트 고유 컨텍스트를 최상위에 온전히 유지한다.
3. 관련 단위 테스트(`tests/test_boot_anchor.py`)를 갱신하여 상단/중간 위치 주석 삭제 및 하단 재배치, 원본 보존, 멱등성을 철저히 검증한다.
4. 프레임워크 버전을 `0.1.8`로 승격한다.

---

## 2. 세부 요구사항 (Detailed Requirements)

1. **기존 주석 삭제 및 하단 추가 로직 전환 (`src/forgeflow/scaffold.py`)**:
   - 정규식 패턴을 사용하여 파일 내 기존에 존재하는 모든 부팅 앵커 마커 블록(`<!-- forgeflow:boot-anchor:start -->` ~ `<!-- forgeflow:boot-anchor:end -->`)을 완전히 삭제.
   - 앵커가 삭제된 순수 본문(`clean_content`)을 추출한 뒤, 파일 맨 마지막에 최신 앵커 블록을 덧붙임:
     `desired_content = clean_content + "\n\n" + anchor_block + "\n"`
   - 파일이 새로 생성되거나 본문이 비어있는 경우 `anchor_block + "\n"` 생성.
   - 이미 파일 맨 마지막에 정확히 앵커가 위치해 있는 경우 불필요한 파일 수정을 방지하고 멱등성(`unchanged`) 유지.
2. **단위 테스트 동기화 (`tests/test_boot_anchor.py`)**:
   - 신규 파일에 부팅 앵커 추가 검증.
   - 상단에 있던 기존 주석이 삭제되고 하단으로 이동하는지 검증 (`test_bind_relocates_existing_anchor_from_top_to_bottom`).
   - 중간에 있던 기존 주석이 삭제되고 하단으로 이동하는지 검증 (`test_bind_relocates_existing_anchor_to_end`).
   - 이미 하단에 있는 경우 멱등성 검증 (`test_bind_is_idempotent_on_repeated_calls`).
   - 주석 해제(`unbind_boot_anchor`) 시 기존 주석이 완전히 제거되고 원본이 복원되는지 검증.
3. **버전 갱신**:
   - `src/forgeflow/_version.py`를 `0.1.8`로 판올림.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: 기존 상단 또는 중간에 작성된 부팅 앵커 주석이 파일에서 완전히 삭제되고, 원본 프로젝트 본문 뒤(맨 마지막)에 최신 앵커 블록이 추가된다.
- **AC-2**: 앵커 블록이 이미 파일 맨 끝에 최신 상태로 존재하는 경우 파일 변경 없이 멱등성(`unchanged`)이 보장된다.
- **AC-3**: `unbind_boot_anchor` 실행 시 앵커 블록이 제거되고 원본 내용이 완벽하게 복원된다.
- **AC-4**: 전체 단위 테스트(284개) 100% Pass 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
- **AC-5**: `src/forgeflow/_version.py` 버전이 `0.1.8`로 승격된다.
