# Task Breakdown: Append Boot Anchor to Root Guides

- **Release ID**: `v0.1.8-append-boot-anchor`
- **Specification**: [spec.md](spec.md)
- **Plan**: [plan.md](plan.md)

---

## 작업 체크리스트 (TDD Atomic Checklist)

- [x] **Task 1: `scaffold.py` 앵커 삭제 및 맨 끝 추가(Delete existing & Append to end) 구현**
  - 기존 주석 위치 무관 완전 삭제 정규식 적용.
  - 파일 맨 끝에 최신 앵커 블록 추가 및 멱등성 보장.
- [x] **Task 2: `tests/test_boot_anchor.py` 단위 테스트 갱신 및 검증**
  - 상단/중간 위치 기존 주석 삭제 및 하단 재배치 검증.
  - 9개 단위 테스트 100% Pass.
- [x] **Task 3: 버전 판올림 (`src/forgeflow/_version.py`)**
  - `__version__ = "0.1.8"` 적용.
- [x] **Task 4: Gate 2 QA Sign-Off 및 Gate 3 릴리즈 밀봉**
  - `QA_SIGNOFF.md` 작성 및 테스트 100% 검증.
  - `RELEASE_SIGNOFF.md` 작성 및 `tasks/completed/` 이동.
  - `forgeflow check --all --strict` 🟢 ALL PASSED 확인.
