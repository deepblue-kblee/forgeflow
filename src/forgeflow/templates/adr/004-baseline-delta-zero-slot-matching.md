# ADR 004: Multi-set Counter 슬롯 매칭 기반 Baseline Review Delta-Zero 정책

- **상태 (Status)**: 승인됨 (Accepted)
- **일자 (Date)**: 2026-11-01
- **결정자 (Deciders)**: Deepblue, AI 어시스턴트
- **대상 버전**: ForgeFlow v0.1.22 ~ v0.1.23

---

## 1. 배경 및 문제 정의 (Context & Problem)

ForgeFlow Gate 2(QA Sign-Off)는 `--strict` 모드에서 모든 코드 스멜(Warning)이 0건일 것을 요구합니다.
그러나 대규모 레거시 코드베이스나 기존 Warning이 잔존하는 환경에서 사소한 1줄 버그픽스나 테스트 픽스처 패치를 수행할 때, 수정 대상 파일 또는 수정된 함수 영역(`MODIFIED_SCOPE`) 내의 기존 Warning까지 전부 해소해야만 Gate 2를 통과할 수 있는 과도한 마찰이 발생했습니다.

이를 위해 `--findings-baseline <ref>` 모드를 도입하여 기준선 대비 신규 경고만 차단하도록 설계했으나:
1. **수정된 함수 내 기존 경고 전면 차단 (초기 v0.1.22)**: 사소한 수정이라도 함수 스코프 내의 기존 경고를 모두 수정하도록 강제하여, 본래 변경 범위를 벗어난 대규모 리팩토링을 유발하고 회귀 위험을 높임.
2. **단순 Fingerprint Set 매칭의 맹점**: 동일 함수 내에 동일 유형의 Warning(예: `Silent Exception`)이 N개 있을 때, 단순 set으로 비교하면 수량이 N+1개로 증가해도 기존 경고로 오인되어 통과되는 치명적 회귀 감지 누락이 발생함.

---

## 2. 결정 사항 (Decision)

1. **Delta-Zero (수량 비증가 통과 허용) 정책 채택**:
   - 수정된 함수 영역(`MODIFIED_SCOPE`) 내에 존재하는 경고라도, 기준선(Baseline)과 비교하여 해당 경고 유형의 **수량이 증가하지 않았다면(`delta <= 0`)** Gate 2 통과를 허용합니다 (`modified_scope_unchanged_warnings`로 분류 및 리포트에 잔존 주의 표기).
2. **Multi-set Counter 기반 슬롯 차감 알고리즘 적용**:
   - `collections.Counter`를 사용하여 기준선의 스멜 fingerprint별 수량을 카운팅하고, 후보(Candidate) 스멜을 하나씩 매칭할 때마다 슬롯을 차감합니다.
   - 기준선 슬롯이 남아있으면 기존 경고로 인정하고, 슬롯이 고갈된 이후 추가로 발견된 동일 fingerprint 경고는 즉시 신규 경고(`new_warnings`)로 분류하여 차단(Fail-Closed)합니다.
3. **신규 경고 추가 시 무조건 Fail-Closed**:
   - 수정된 함수 내에서 새로운 규칙 위반이 발생하거나 기존 경고 수량이 1건이라도 증가하면 즉시 Gate 2를 차단합니다.

---

## 3. 결과 및 영향 (Consequences)

- **긍정적 영향**:
  - 사소한 국소 패치 시 무리한 코드 재작성 압박을 원천 해소하여 에이전트 및 개발자의 생산성과 변경 격리성을 극대화.
  - 슬롯 차감 방식을 통해 동일 경고 유형의 누적/증가를 1건의 오차도 없이 엄격히 차단하여 안전성과 엄격성(Strictness)을 동시에 보장.
- **수반 사항**:
  - 수정된 함수 내 잔존 Warning은 리포트에 명확히 표기되어 기술 부채가 투명하게 추적됨.
