# Architecture & Technical Plan: Delta-Zero Modified Scope Review

- **Release ID**: `v0.1.23-delta-zero-baseline-review`
- **Target Component**: `src/forgeflow/reviewer.py`, `src/forgeflow/renderer.py`, `tests/test_reviewer.py`

---

## 1. 아키텍처 개요 (Architectural Overview)

```text
[Baseline Warnings] ──> collections.Counter(fingerprints) ──> baseline_fp_counts
                                                                    │
[Candidate Warnings] ──> for each warning s (fp = s.fingerprint)   │
                               │                                    │
                  ┌────────────┴────────────┐                       │
       [baseline_fp_counts[fp] > 0]    [count == 0]                 │
                  │                          │                      │
       [Slot Match: count -= 1]         [NEW / REGRESSED]           │
                  │                          │                      │
       ┌──────────┴──────────┐          (🔴 차단 대상)              │
[s.scope in mod_scopes]   [else]                                    │
       │                    │                                       │
[MODIFIED_SCOPE_EXISTING] [EXEMPT]                                  │
       │                    │                                       │
   (🟡 주의 표시)      (🟢 면제 승인)                               │
       └──────────┬─────────┘                                       │
                  ▼                                                 ▼
      [Gate 2 Strict 판정: effective_critical == 0 and new_warnings == 0]
```

---

## 2. 핵심 알고리즘 설계 (Key Algorithms)

- **Counter 기반 Multi-set 슬롯 매칭**:
  - `baseline_fp_counts = Counter(bs.fingerprint(rel_p) for bs in baseline_all_smells if bs.severity == "WARNING")`
  - 후보 코드의 각 Warning 검사 시 슬롯이 남아있으면 1개 차감하고 기존 경고로 인정(수정 스코프에 속하면 `modified_scope_smells`, 아니면 `exempt_smells`).
  - 슬롯이 남아있지 않으면(기존 수량 초과 또는 신규 스멜) `new_smells`에 추가.
- **Strict 통과 조건**:
  - `passed = effective_critical == 0 and new_w == 0`
