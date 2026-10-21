# Task Breakdown: Interactive Upgrade Prompt and Force Option

- **Release ID**: `v0.1.9-interactive-upgrade-prompt`
- **Specification**: [spec.md](spec.md)
- **Plan**: [plan.md](plan.md)

---

## 작업 체크리스트 (TDD Atomic Checklist)

- [x] **Task 1: `src/forgeflow/cli.py` 대화형 프롬프트 및 비교 정보 출력 구현**
  - 현재 버전과 최신 버전 비교 출력.
  - `force=False`일 때 `input()` 기반 `y/n` 확인 질문 추가.
  - `force=True` 시 확인 질문 없이 바로 진행.
- [x] **Task 2: `tests/test_upgrade_cli.py` 테스트 케이스 추가 및 검증**
  - `y` 입력 시 업그레이드 실행 검증.
  - `n` 입력 시 업그레이드 취소 검증.
  - `--force` 플래그 시 프롬프트 생략 검증.
- [x] **Task 3: 버전 판올림 (`src/forgeflow/_version.py`)**
  - `__version__ = "0.1.9"` 적용.
- [x] **Task 4: Gate 2 QA Sign-Off 및 Gate 3 릴리즈 밀봉**
  - `QA_SIGNOFF.md` 작성 및 테스트 100% 검증.
  - `RELEASE_SIGNOFF.md` 작성 및 `tasks/completed/` 이동.
  - `forgeflow check --all --strict` 🟢 ALL PASSED 확인.
