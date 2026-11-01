# Architecture & Technical Plan: Align Baseline-Aware Gate 2 with SHA-Free Lifecycle Seals

- **Release ID**: `v0.1.24-align-baseline-review-sha-free-seals`
- **Target Components**:
  - `src/forgeflow/harness.py`
  - `src/forgeflow/lifecycle.py`
  - `src/forgeflow/cli.py`
  - `src/forgeflow/templates/QA_SIGNOFF.md`
  - `src/forgeflow/templates/RELEASE_SIGNOFF.md`
  - `src/forgeflow/spec/GATES_AND_LOOPS.md`
  - `docs/spec/GATES_AND_LOOPS.md`
  - `src/forgeflow/spec/FLOW_SPEC.md`
  - `docs/spec/FLOW_SPEC.md`
  - `tests/test_lifecycle_harness.py`
  - `tests/test_lifecycle_cli.py`
  - `tests/test_reviewer.py`

---

## 1. 아키텍처 개요 (Architectural Overview)

```text
               [Gate 2 Review Policy]
              /                      \
      [raw strict]            [baseline-aware strict]
      (Warning 0건)         (Critical 0 & New Warning 0)
              \                      /
               ▼                    ▼
             [Gate 2 QA Sign-Off (QA_SIGNOFF.md)]
                           │
             [Evidence v2: Binding-Policy]
            /                             \
     [git-sha (default)]              [sha-free]
            │                              │
  (Base-SHA / QA-SHA hex)          (Base-SHA / QA-SHA: sha-free)
  (Reviewer/Verification sha)      (Reviewer/Verification sha-free/omitted)
            │                              │
            ▼                              ▼
  [lifecycle package-review]       [lifecycle package-review]
  (Requires local commit)          (Verifies clean worktree & artifacts)
            │                              │
            ▼                              ▼
  [Gate 3 RELEASE_SIGNOFF.md]      [Gate 3 RELEASE_SIGNOFF.md]
  (User Go/No-Go & Manifest)       (User Go/No-Go & Manifest)
            │                              │
            ▼                              ▼
  [lifecycle seal]                 [lifecycle seal]
  (Candidate commit binding)       (Manifest & Clean worktree seal)
            │                              │
            ▼                              ▼
     [Terminal Audit]                 [Terminal Audit]
     (Check commit extant)            (Check Manifest & Clean worktree)
            │                              │
            ▼                              ▼
  [lifecycle complete]             [lifecycle complete]
```

---

## 2. 세부 설계 (Detailed Component Design)

### 2.1 Evidence v2 파싱 및 유효성 검증 (`harness.py`)
- `_parse_evidence_v2(text)`:
  - `Binding-Policy` 필드를 허용(선택적 singleton). 값은 `git-sha` 또는 `sha-free`.
  - `Base-SHA`, `QA-SHA`는 기본 singleton 유지하되, `Binding-Policy: sha-free`인 경우 또는 두 필드의 값이 `sha-free` / `none` / `SHA-FREE`인 경우 SHA 형태 검증 완화.
- `_validate_evidence_v2(release_id, qa_text, evidence)`:
  - `binding_policy = str(evidence.get("Binding-Policy", "git-sha")).lower()`
  - `qa_sha = str(evidence.get("QA-SHA", ""))`
  - 만약 `binding_policy == "sha-free"` 또는 `qa_sha.lower() in {"sha-free", "none"}`:
    - `Base-SHA`와 `QA-SHA`는 40자리 hex 대신 `sha-free` / `none` / 유효한 문자열 허용.
    - `Reviewer` 항목의 `qa-sha`: `qa-sha` 필드가 `sha-free`이거나, `qa-sha` 키 자체가 생략된 경우 허용.
    - `Verification` 항목의 `qa-sha`: `qa-sha` 필드가 `sha-free`이거나, `qa-sha` 키 자체가 생략된 경우 허용.
  - 그렇지 않은 경우(기존 `git-sha` 모드):
    - 기존의 엄격한 40자리 hex SHA 대조 로직 100% 실행 (하위 호환).

### 2.2 라이프사이클 전이 엔진 (`lifecycle.py` & `harness.py`)
- `lifecycle.py`:
  - `mark_package_review_pending(*, qa_sha: str)`:
    - `qa_sha.lower() == "sha-free"` 또는 40자리 hex SHA 허용.
  - `seal_package(*, release_candidate_sha: str, package_manifest_sha256: str)`:
    - `release_candidate_sha.lower() == "sha-free"` 또는 40자리 hex SHA 허용.
  - `completion_ready()`:
    - `qa_sha == "sha-free"` 및 `candidate_sha == "sha-free"`인 경우, `qa_sha_missing` 및 `candidate_missing` 에러를 건너뜀.
- `harness.py`:
  - `lifecycle_package_review(release_id, qa_sha)`:
    - `qa_sha`가 주어지지 않거나 `"sha-free"`인 경우, `QA_SIGNOFF.md`의 evidence가 `sha-free` 정책인지 확인.
    - `is_sha_free`:
      - `_is_local_commit` 검사를 생략하고, working tree가 clean 상태인지 검사(`ReviewScanner.is_clean_worktree`).
      - `controller.mark_package_review_pending(qa_sha="sha-free")`.
  - `lifecycle_seal(release_id, release_candidate_sha)`:
    - `release_candidate_sha`가 주어지지 않거나 `"sha-free"`인 경우:
      - `is_sha_free` 확인: `_has_v2_candidate_binding` 검사를 생략하고 clean working tree 확인.
      - `controller.seal_package(release_candidate_sha="sha-free", package_manifest_sha256=manifest)`.
  - `_validate_v2_package_evidence(...)`:
    - `qa_sha`가 `"sha-free"`인 경우 `qa_sha_mismatch` 대신 둘 다 `sha-free`이면 일치 판정.
    - `require_terminal_state`:
      - `candidate == "sha-free"`인 경우 `candidate_sha_not_local_commit` 검사를 건너뛰고 매니페스트 및 status COMPLETE 검증.

### 2.3 CLI 서브커맨드 (`cli.py`)
- `package-review`:
  - `qa_sha_pos` 및 `--qa-sha`를 선택적(Optional)으로 처리.
  - 미입력 시 `QA_SIGNOFF.md`를 조회하여 `sha-free` 정책이면 자동으로 `qa_sha="sha-free"`로 전달. `--sha-free` 플래그 명시적 지원.
- `seal`:
  - `candidate_sha_pos` 및 `--candidate-sha`를 선택적으로 처리.
  - 미입력 시 `sha-free` 정책이면 자동으로 `release_candidate_sha="sha-free"`로 전달. `--sha-free` 플래그 명시적 지원.

### 2.4 공식 사양서 및 템플릿
- `QA_SIGNOFF.md`:
  - 검토 정책 선택지(raw strict vs baseline-aware strict) 및 기준선 통계 기재란 신설.
  - Evidence v2에 `Binding-Policy: sha-free` 가이드 추가.
- `RELEASE_SIGNOFF.md`:
  - QA-SHA 바인딩 강제 문구를 완화하고 매니페스트 및 100% 테스트 무결성 기반 승인 명시.
- `docs/spec/GATES_AND_LOOPS.md` & `src/forgeflow/spec/GATES_AND_LOOPS.md`:
  - Gate 2 사양에 raw strict와 baseline-aware strict의 공식 정책 및 기준선 승인 절차 반영.
  - SHA-free 라이프사이클 정책 반영.
- `docs/spec/FLOW_SPEC.md` & `src/forgeflow/spec/FLOW_SPEC.md`:
  - 플로우 명세에 SHA-free 패키지 리뷰 및 밀봉 수명주기 반영.
