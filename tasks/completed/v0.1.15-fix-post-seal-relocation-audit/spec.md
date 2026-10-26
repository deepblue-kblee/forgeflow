# Feature Specification: Allow Committed Completion Relocation in Lifecycle Audit (Issue #5)

- **Release ID**: `v0.1.15-fix-post-seal-relocation-audit`
- **Created Date**: 2026-10-26
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Lifecycle Audit)**
- **Related Issue**: GitHub Issue #5 ([Bug] Committed completion relocation fails post-seal lifecycle audit in v0.1.14)

---

## 1. 개요 및 목적 (Overview & Purpose)

ForgeFlow v0.1.14에서 릴리즈의 Gate 1/2/3 증적이 완비된 후 패키지를 밀봉(`lifecycle seal`)하고 완료(`lifecycle complete`)하면, 패키지 디렉터리가 `tasks/in-progress/<release-id>`에서 `tasks/completed/<release-id>`로 원자적으로 이동(Relocation)된다.
그러나 이후 이 정상적인 완료 이동 커밋(M)을 수행한 뒤 터미널 감사(`forgeflow check --lifecycle <release-id> --strict`)를 실행하면, 이동된 패키지 파일들의 바이트가 100% 동일함에도 불구하고 사후 감사 엔진(`_candidate_disallowed_paths`)이 이를 `release_candidate_range_invalid`로 잘못 거부(False Positive)하는 결함이 존재한다.

본 릴리즈의 목적은 다음과 같다:
1. **완료 패키지 이동 인식 및 바이트 무결성 검증 (Byte-Identical Relocation Verification)**:
   - `candidate..current_head` 범위에서 승인된 릴리즈 패키지 디렉터리가 `in-progress`에서 `completed`로 이동한 내역을 감지.
   - 후보 커밋(`candidate`) 시점의 패키지 파일 트리와 현재 HEAD(`current_head`)의 완료 패키지 파일 트리를 Git Blob SHA 수준에서 대조하여, 파일의 추가·삭제·변조 없이 100% 바이트 단위로 동일하게 이동되었는지 엄격히 검증.
2. **사후 감사 화이트리스트 확장**:
   - 바이트 동일성이 입증된 완료 이동 경로에 한하여 사후 변경(`candidate..current_head`) 허용 경로로 인정하여 `release_candidate_range_invalid` 오탐을 원천 해소.
3. **엄격한 Fail-Closed 불변성 유지**:
   - 런타임 코드(`src/**`), 테스트(`tests/**`), 스크립트 수정은 물론, 패키지 파일 내용의 1바이트 변조, 무인가 파일 추가, 타 릴리즈의 이동 등이 발생할 경우 즉각 거부(`disallowed`).
4. **회귀 테스트 완비**:
   - 정상 `seal -> complete -> commit -> check --lifecycle --strict` 전 과정 및 변조/추가/타 릴리즈 혼입 시의 fail-closed 차단을 검증하는 회귀 테스트 추가.

---

## 2. 세부 요구사항 (Detailed Requirements)

### 2.1 Git 트리 대조를 통한 바이트 동일 완료 이동 검증 (`harness.py`)
- `HarnessEngine`에 `_tree_files_at_commit(commit, directory_path)` 메서드 구현:
  - `git ls-tree -r -z <commit> -- <directory_path>`를 호출하여 `<rel_path>: <blob_sha>` 맵을 추출.
  - OS 오류 또는 비정상 반환 시 빈 딕셔너리를 반환하여 안전하게 fail-closed 동작.
- `_find_verified_completion_relocation_paths(release_id, candidate, current_head)` 메서드 구현:
  - 지원되는 태스크 루트(`tasks`, `ff-tasks`, 및 설정된 커스텀 tasks 디렉터리)를 순회.
  - 후보 커밋(`candidate`) 시점의 `src_dir`(`{pfx}/in-progress/{release_id}`) 파일 목록과 Blob SHA를 조회.
  - 현재 HEAD(`current_head`) 시점의 `dst_dir`(`{pfx}/completed/{release_id}`) 파일 목록과 Blob SHA를 조회.
  - 다음 3대 조건을 모두 만족할 때만 바이트 동일 이동으로 판정:
    1. 후보 커밋 시점의 `src_dir` 파일 맵이 비어있지 않음 (`len(candidate_files) > 0`).
    2. 현재 HEAD 시점의 `src_dir`에 잔여 파일이 없음 (`len(head_src_files) == 0`).
    3. 현재 HEAD 시점의 `dst_dir` 파일 맵이 후보 시점의 `src_dir` 파일 맵과 100% 일치 (`head_dst_files == candidate_files`).
  - 조건을 충족한 경우에만 이동 관련 경로 집합(`{f"{src_dir}/{k}" ...} | {f"{dst_dir}/{k}" ...}`)을 반환.

### 2.2 사후 변경 경로 화이트리스트 적용 (`_candidate_disallowed_paths`)
- `candidate != current_head` 검사 시:
  - 기존 허용 경로: `.forgeflow/lifecycle/{release_id}.json`, `docs/session-state/**`, `.lock` 파일.
  - 추가 허용 경로: `_find_verified_completion_relocation_paths`로 검증된 해당 릴리즈의 완료 이동 파일 경로.
  - 위 허용 범위 외의 파일(코드, 테스트, 미승인 문서, 타 릴리즈 파일 등)이 하나라도 존재하면 즉시 `disallowed`에 추가.

### 2.3 `lifecycle_complete` 태스크 디렉터리 호환성 강화
- `parts[0] in ("tasks", "ff-tasks")` 외에도 `.forgeflow.json`에 정의된 커스텀 tasks 디렉터리가 있을 경우 완료 이동 대상으로 안전하게 인식.

### 2.4 버전 승격 및 사양서 반영
- `src/forgeflow/_version.py`를 `0.1.15`로 판올림.
- `docs/spec/CHANGELOG.md` 및 `src/forgeflow/templates/spec/CHANGELOG.md`에 `[0.1.15] - 2026-10-26` 변경 이력 반영.

---

## 3. 계획된 변경 경로 (Planned Paths) - Tier 3

- `src/forgeflow/_version.py`
- `src/forgeflow/harness.py`
- `docs/spec/CHANGELOG.md`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `tests/test_candidate_seal.py`
- `tasks/in-progress/v0.1.15-fix-post-seal-relocation-audit/**`

---

## 4. 인수 조건 (Acceptance Criteria)

- [ ] **AC-1**: `lifecycle seal` 완료 후 `lifecycle complete`로 인해 `tasks/in-progress/{release-id}`에서 `tasks/completed/{release-id}`로 이동된 패키지가 커밋되었을 때, `_candidate_disallowed_paths` 및 `_has_v2_candidate_binding`이 `disallowed=[]` 및 `True`를 반환한다.
- [ ] **AC-2**: 이동 후 `tasks/completed/{release-id}` 내 문서 내용이 단 1바이트라도 변경되거나, 신규 파일이 추가되거나, 원본 디렉토리에 잔여 파일이 남아있는 경우 즉시 `disallowed`로 판정하여 fail-closed 차단한다.
- [ ] **AC-3**: 타 릴리즈 패키지의 이동이나 런타임 코드(`src/**`), 테스트(`tests/**`)의 변경이 포함된 경우 즉시 `disallowed`로 판정한다.
- [ ] **AC-4**: `seal -> complete -> commit -> check_lifecycle_evidence(strict=True)`의 전체 실전 라이프사이클 회귀 테스트가 통과한다.
- [ ] **AC-5**: 기존 298개 테스트 및 신규 회귀 테스트가 100% Pass한다.
- [ ] **AC-6**: `forgeflow check --all --strict` 거버넌스 감사가 🟢 ALL PASSED를 달성하고, Tier 3 3대 패널 심사를 완료한다.
