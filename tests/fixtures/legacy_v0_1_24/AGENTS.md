<!-- forgeflow:boot-anchor:start -->
## 🌊 ForgeFlow Session Boot Sequence (Harness Governance)

작업 착수 전 필수 확인 및 준수:
1. **헌법 확인**: `.specify/memory/constitution.md` 원칙 준수
2. **사양서 색인 참조**: `.forgeflow/spec/README.md` 확인 후 해당 작업 단계 사양서만 선별 참조
3. **최신 버전 동기화 & 기억 리셋**: `.forgeflow/spec/VERSION` 확인. 버전 변경 감지 또는 세션 진입 시 과거 버전 지식 즉시 폐기(Amnesia) 및 `README.md` 재독 필수
4. **버전 격리**: `~/.local/share/forgeflow/packages/` 내 과거 버전 일체 참조 금지 (`current` 최신본만 사용)
<!-- forgeflow:boot-anchor:end -->
