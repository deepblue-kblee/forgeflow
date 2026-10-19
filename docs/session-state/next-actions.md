# Next Actions

## 다음 할 일 (Next Tasks)

1. **외부 타깃 프로젝트 실전 적용 및 도그푸딩**:
   - 실제 개발 대상 외부 저장소에서 `curl -sSL https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh | bash`를 실행하여 환경 구성.
   - `/setup-forgeflow` 스킬을 호출하여 신규 프로젝트 스캐폴딩(`.forgeflow.json`, `.specify/`, `tasks/`) 검증.
   - Spec Kit 인터뷰(`/speckit.specify`, `/speckit.clarify`)부터 `forgeflow check --stage 2` Fail-Closed 게이트키퍼 차단 및 구현 완주까지 실전 도그푸딩 수행.

2. **Spec Kit CLI 전역 툴체인(`uv tool install specify-cli`) 연동 고도화**:
   - `specify-cli` 전역 툴체인 환경과의 추가 호환성 및 편의 기능 검토.
