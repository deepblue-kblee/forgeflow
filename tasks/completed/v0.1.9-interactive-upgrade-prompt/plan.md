# Implementation Plan: Interactive Upgrade Prompt and Force Option

- **Release ID**: `v0.1.9-interactive-upgrade-prompt`
- **Target Specification**: [spec.md](spec.md)
- **Approved Date**: 2026-10-21

---

## 1. 아키텍처 및 상세 설계 (Architecture & Design)

### 1.1 `src/forgeflow/cli.py`의 `handle_upgrade` 로직 개선

1. **버전 비교 출력**:
   `not as_json`일 때:
   ```python
   print(f"🔍 Checking ForgeFlow version...")
   print(f"• Current version: v{__version__}")
   print(f"• Latest version:  v{remote_version}")
   print()
   ```

2. **최신 상태 분기**:
   ```python
   if not is_upgrade_available and not force:
       if as_json:
           print(json.dumps(...))
       else:
           print(f"✅ ForgeFlow is already up to date (v{__version__}). (Use --force to reinstall)")
       return 0
   ```

3. **대화형 승인 프롬프트**:
   `if not force and not as_json:` 조건에서:
   ```python
   action_label = "upgrade to" if is_upgrade_available else "reinstall"
   prompt_msg = f"Do you want to {action_label} v{remote_version}? [y/N]: "
   try:
       answer = input(prompt_msg).strip().lower()
   except (EOFError, KeyboardInterrupt):
       print("\nUpgrade cancelled.")
       return 0

   if answer not in ("y", "yes"):
       print("Upgrade cancelled.")
       return 0
   ```

4. **설치 프로세스 진행**:
   기존 다운로드 및 `bash installer --force` 실행 유지.

### 1.2 `tests/test_upgrade_cli.py` 테스트 케이스 확장

- `test_upgrade_interactive_prompt_yes`: `builtins.input`에 `"y"` 반환 모의, 설치 정상 호출 검증.
- `test_upgrade_interactive_prompt_no`: `builtins.input`에 `"n"` 반환 모의, 설치 미호출 및 0 반환 검증.
- `test_upgrade_force_skips_prompt`: `parse_forgeflow_args(["upgrade", "--force"])` 실행 시 `input` 호출 없이 바로 설치 호출 검증.
- 기존 `--json` 및 `--check` 테스트 정상 통과 유지.

### 1.3 버전 판올림

- `src/forgeflow/_version.py`: `__version__ = "0.1.9"`

---

## 2. 검증 전략 (Verification Strategy)

1. `PYTHONPATH=src python3 -m unittest tests/test_upgrade_cli.py` 단위 테스트 검증.
2. `.venv/bin/pytest` 전체 테스트 스위트 100% Pass 검증.
3. `forgeflow check --all --strict` 실행하여 8개(신규 포함 9개) 릴리즈 전수 통과 확인.
