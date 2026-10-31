# Gate 1 Review Sign-Off: Relocate Configuration to .forgeflow/config.json with Update Migration

- **Release ID**: `v0.1.20-relocate-config-to-forgeflow-dir`
- **Review Date**: 2026-10-31
- **Risk Tier**: **Tier 3 (Core / Governance Configuration & Implementation Control)**
- **Target Specification**: [spec.md](spec.md)
- **Gate 1 Verdict**: **APPROVED**

---

## 1. Governance Classification & Risk Tiering

- **분류**: Tier 3 (Core / Governance Configuration & Implementation Control)
- **근거**: 프레임워크의 핵심 프로젝트 설정 파일 저장 위치(`.forgeflow/config.json`) 및 스캐폴더, 런너, 스캐너, 진단기, 업데이트 마이그레이션 로직 전반을 변경함.
- **필수 승인 요건**: 3대 패널(보안, 안정성, 유지보수성) 독립 심사 및 사용자 요구사항 반영 검토 완료 ("APPROVED").

---

## 2. 3대 패널 독립 심사 결과 (Panel Review)

### 2.1 보안 패널 (Security Panel: PASS)
- **경로 탈출 및 변조 방지**: 설정 파일 대상 경로를 `root / ".forgeflow" / "config.json"`으로 한정하고, 저널링 및 파일 쓰기 시 엄격한 경로 안전성 검증 수행.
- **Fail-Closed 예외 처리**: 기존 설정 마이그레이션 시 손상되거나 비정상적인 JSON은 안전하게 에러를 발생시키고 기존 파일을 함부로 삭제하지 않음.

### 2.2 안정성 패널 (Reliability Panel: PASS)
- **하위 호환성 보장 (Graceful Fallback)**: 구버전 리포지토리에서 `forgeflow update`를 수행하기 전이라도 루트의 `.forgeflow.json`을 폴백으로 읽어 시스템 장애를 방지.
- **마이그레이션 원자성**: `forgeflow update` 시 새 파일(`.forgeflow/config.json`)을 성공적으로 기록한 후 구버전 파일을 언링크(unlink)하여 설정 유실을 원천 차단.

### 2.3 유지보수성 패널 (Maintainability Panel: PASS)
- **루트 디렉터리 정돈 (Clean Root)**: 프로젝트 루트를 어지럽히지 않고 `.forgeflow/` 하위로 설정을 일원화하여 모듈성 향상.
- **Zero-Dependency 원칙 준수**: 파이썬 표준 라이브러리(`json`, `pathlib`)만으로 구현.

---

## 3. 사전 구현 검증 체크리스트 (Pre-Implementation Checklist)

- [x] 프레임워크 5대 불변 헌법 준수
- [x] 5대 인수 조건(AC-01 ~ AC-05) 정의 완료
- [x] 계획된 변경 경로(Planned Paths) 한정 완료
- [x] 사용자 요구사항(설정 파일 위치 이전 및 update 마이그레이션) 반영 완료
- [x] Stage 2 기술 설계(`plan.md`) 및 태스크 분해(`tasks.md`) 연계 준비 완료

---

## 4. 최종 판정 (Gate 1 Verdict)

- **Gate 1 Status**: **APPROVED**
- **Approver**: Security, Reliability, Maintainability Independent Panel & User Explicit Request
- **Next Stage**: Stage 2 (기술 설계 및 작업 분해)
