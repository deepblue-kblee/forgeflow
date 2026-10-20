# Architecture Plan: Removal of Legacy Update Command & Obsolete Catalogs

- **Release ID**: `v0.1.4-remove-legacy-update-command`
- **Status**: APPROVED ARCHITECTURE
- **Risk Tier**: Tier 3 (Critical)

---

## 1. 아키텍처 및 정리 설계 (Architecture Overview)

### 1.1 CLI 서브커맨드 정리 (`cli.py`)
- `from .update import apply as apply_update, inspect as inspect_update` 임포트 제거.
- `update_parser = subparsers.add_parser("update", ...)` 파서 등록 코드 제거.
- `if parsed.command == "update": ...` 디스패치 분기 제거.
- `forgeflow --help`에 노출되는 명령어 목록: `init, release, check, lifecycle, review, version, upgrade, migrate, task, status, doctor, diagnose, issue`.

### 1.2 모듈 및 자산 삭제
- `src/forgeflow/update.py` 영구 삭제.
- `src/forgeflow/bundle_catalog.py` 영구 삭제.
- `src/forgeflow/catalog_oracles/` 하위 모듈 영구 삭제.
- `tests/test_update.py` 삭제.
- `tests/test_cli.py`에서 `test_forgeflow_update_cli_does_not_raise_attribute_error` 테스트 메서드 제거.

---

## 2. 검증 계획
- `forgeflow --help` 및 `forgeflow update` 실행으로 제거 검증.
- 잔여 263개 테스트 스위트 전수 실행 (`pytest`).
- `forgeflow check --all --strict` 하네스 감사 실행.
