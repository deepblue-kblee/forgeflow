# Gate 1 Specification Sign-Off: Redefining ForgeFlow Update Command & Facade Integration

- **Release ID**: `v0.1.5-redefine-update-command-and-facade`
- **Review Date**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core CLI Interface / Public Interface)**
- **Target Specification**: [spec.md](spec.md)
- **Gate 1 Verdict**: **APPROVED**

---

## 1. 리스크 티어링 심사 (Risk Tiering Evaluation)

- **도메인**: CLI 공개 인터페이스, 로컬 리포지토리 파일 수정 및 스캐폴딩 갱신, 에이전트 스킬 지침
- **판정 근거**: 신규 CLI 서브커맨드(`update`)를 재정의하고 프로젝트 내부 템플릿/스크립트를 덮어쓰는 작업이므로 **Tier 3 (Critical)**로 분류하고 3대 패널 심사를 수행한다.

---

## 2. 3대 패널 독립 심사 결과 (Independent Review Panel)

### 2.1 보안 관점 (Security Reviewer: PASS)
- **심사 의견**:
  1. `update` 명령어가 프로젝트 루트 외의 상위 디렉터리나 임의 경로를 침범하지 않도록 `TemplateScaffolder`의 기존 경로 검증 가드를 100% 거쳐야 함.
  2. 업데이트 대상 스크립트(`0o755`)는 번들된 내부 리소스에서만 복사되어야 하며 외부 임의 주입이 없어야 함.
- **판정**: **PASS**

### 2.2 안정성 관점 (Reliability Reviewer: PASS)
- **심사 의견**:
  1. 가장 중요한 점은 사용자의 진행 중/완료된 릴리즈 산출물(`tasks/in-progress/`, `tasks/completed/`)이 절대 손상되거나 초기화되지 않아야 함.
  2. `.forgeflow.json`이 없는 비-ForgeFlow 디렉터리에서 실수로 실행될 경우 즉시 실행을 중단하고 변경을 일으키지 않아야 함.
- **판정**: **PASS**

### 2.3 유지보수성 관점 (Maintainability Reviewer: PASS)
- **심사 의견**:
  1. `forgeflow upgrade`(전역)와 `forgeflow update`(로컬)의 대칭성이 확립되어 직관성이 극대화됨.
  2. `/update-forgeflow` 스킬 지침이 두 CLI 명령의 조합으로 단순화되어 스킬 유지보수 부담이 완전히 해소됨.
- **판정**: **PASS**

---

## 3. 계획된 변경 범위 (Planned Scope of Changes)

- `src/forgeflow/scaffold.py` (`update_repo_governance`)
- `src/forgeflow/cli.py` (`update` 서브커맨드)
- `scripts/install-skills.sh`
- `~/.agents/skills/update-forgeflow/SKILL.md`
- `tests/test_update_cli.py`
- `README.md`
- `docs/spec/FLOW_SPEC.md`
- `src/forgeflow/_version.py`

---

## 4. 최종 게이트 승인 서명 (Final Sign-Off)

- **Gate 1 Status**: **APPROVED**
- **Approved by**: AI Agent Panel (Antigravity) & User Explicit Instruction ("승인")
- **Next Stage**: Stage 2 (기술 설계 `plan.md`) 및 Stage 3 (원자적 태스크 분해 `tasks.md`) 착수 허용
