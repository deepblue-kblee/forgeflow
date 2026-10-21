# Implementation Plan: Append Boot Anchor to Root Guides

- **Release ID**: `v0.1.8-append-boot-anchor`
- **Target Specification**: [spec.md](spec.md)
- **Approved Date**: 2026-10-21

---

## 1. 아키텍처 및 변경 설계 (Architecture & Design)

### 1.1 `src/forgeflow/scaffold.py`의 `bind_boot_anchor` 개선

- 정규식 패턴 `anchor_pattern = re.compile(rf"\n*{re.escape(cls.BOOT_ANCHOR_START)}.*?{re.escape(cls.BOOT_ANCHOR_END)}\n*", re.DOTALL)` 컴파일.
- 파일 내 기존에 작성되어 있던 모든 위치의 부팅 앵커 주석을 `clean_content = anchor_pattern.sub("\n\n", content).strip()`으로 완전 제거.
- 원본 본문이 존재하는 경우 말미에 최신 앵커 블록 덧붙임:
  `desired_content = clean_content + "\n\n" + anchor_block + "\n"`
- 파일 내용이 이미 `desired_content`와 완전히 일치할 경우 디스크 쓰기 없이 `unchanged`로 반환(멱등성).
- 불일치 시 파일에 `desired_content`를 기록하고 `updated` 반환.

### 1.2 `unbind_boot_anchor` 개선

- 동일한 정규식을 사용하여 마커가 어디에 위치하든 깨끗하게 제거하고 원본 텍스트 복원.

### 1.3 `tests/test_boot_anchor.py` 테스트 갱신

- 신규 생성 시 앵커 생성 검증.
- 기존 파일 맨 끝에 앵커 추가 검증 (`test_bind_appends_to_existing_agents_md_preserving_content`).
- 공백 파일에 깔끔하게 앵커 추가 검증 (`test_bind_appends_to_whitespace_file_cleanly`).
- 중간에 있던 앵커가 삭제되고 맨 뒤로 이동하는지 검증 (`test_bind_relocates_existing_anchor_to_end`).
- 상단에 있던 앵커가 삭제되고 맨 뒤로 이동하는지 검증 (`test_bind_relocates_existing_anchor_from_top_to_bottom`).
- 멱등성 및 원복 테스트 검증.

### 1.4 `src/forgeflow/_version.py` 버전 판올림

- `__version__ = "0.1.8"`

---

## 2. 검증 전략 (Verification Strategy)

1. `PYTHONPATH=src python3 -m unittest tests/test_boot_anchor.py` 실행하여 부팅 앵커 단위 테스트 9개 전수 통과 확인.
2. `.venv/bin/pytest` 전체 284개 테스트 통과 확인.
3. `forgeflow check --all --strict` 실행하여 거버넌스 감사 통과 확인.
