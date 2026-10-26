# Implementation Plan: Allow Committed Completion Relocation in Lifecycle Audit

- **Release ID**: `v0.1.15-fix-post-seal-relocation-audit`
- **Created Date**: 2026-10-26
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Lifecycle Audit)**

---

## 1. 아키텍처 및 세부 설계 (Architecture & Design)

### 1.1 Git Blob 수준의 바이트 동일 트리 비교 엔진 (`HarnessEngine`)
- **구현 위치**: `src/forgeflow/harness.py`
- **`_tree_files_at_commit(self, commit: str, directory_path: str) -> Dict[str, str]`**:
  - `git ls-tree -r -z <commit> -- <directory_path>`를 안전하게 실행.
  - 출력된 레코드를 파싱하여 `{rel_path: blob_sha}` 딕셔너리로 반환.
  - 서브프로세스 에러, 빈 출력, 비정상 포맷 시 `{}`를 반환하여 안전하게 fail-closed 보장.
- **`_find_verified_completion_relocation_paths(self, release_id: str, candidate: str, current_head: str) -> Set[str]`**:
  - 검사 대상 접두사: `("tasks", "ff-tasks")` 및 설정된 커스텀 tasks 디렉터리.
  - 각 접두사별:
    - `src_dir = f"{pfx}/in-progress/{release_id}"`
    - `dst_dir = f"{pfx}/completed/{release_id}"`
    - `candidate_files = self._tree_files_at_commit(candidate, src_dir)`
    - 만약 `candidate_files`가 존재하면:
      - `head_src_files = self._tree_files_at_commit(current_head, src_dir)`
      - `head_dst_files = self._tree_files_at_commit(current_head, dst_dir)`
      - 만약 `not head_src_files and candidate_files == head_dst_files`:
        - 바이트 단위 완전 일치 확인 완료.
        - 허용 경로 집합 `{f"{src_dir}/{k}" for k in candidate_files} | {f"{dst_dir}/{k}" for k in candidate_files}` 반환.
  - 조건을 충족하지 못하면 빈 `set()` 반환.

### 1.2 사후 변경 경로 감사 로직 교정 (`_candidate_disallowed_paths`)
- `current_head != candidate`일 때:
  - `changed_post`의 각 경로에 대해:
    - 허용: `allowed_post` (`.forgeflow/lifecycle/{release_id}.json`)
    - 허용: `docs/session-state/*`
    - 허용: `.forgeflow/` 관련 `.lock` 파일
    - 허용: `relocation_paths` (바이트 동일 검증 통과한 완료 패키지 이동 경로)
    - 그 외 모든 파일: `disallowed.append(path)`

### 1.3 `lifecycle_complete` 태스크 디렉터리 탐색 보강
- `parts[0] in ("tasks", "ff-tasks")` 검사에 `configured` tasks dir 지원 추가.

### 1.4 버전 승격 및 사양서 갱신
- `src/forgeflow/_version.py`: `__version__ = "0.1.15"`
- `docs/spec/CHANGELOG.md` & `src/forgeflow/templates/spec/CHANGELOG.md`:
  - `[0.1.15] - 2026-10-26` 항목 추가
  - 패키지 완료 이동 사후 감사 오탐 해소 요약 기재

### 1.5 회귀 테스트 스위트 보강
- `tests/test_candidate_seal.py`:
  1. `test_post_candidate_committed_completion_relocation_allowed`: 정상 이동 커밋 시 `disallowed=[]` 및 `_has_v2_candidate_binding` 통과.
  2. `test_post_candidate_relocation_fails_if_package_mutated`: 이동 후 내용 1바이트 변조 시 `disallowed` 차단.
  3. `test_post_candidate_relocation_fails_if_extra_file_added`: 이동 후 신규 파일 추가 시 `disallowed` 차단.
  4. `test_post_candidate_relocation_fails_if_source_files_remain`: 원본 디렉토리에 파일 잔류 시 `disallowed` 차단.
  5. `test_post_candidate_relocation_fails_if_unrelated_release`: 타 릴리즈 이동 시 `disallowed` 차단.
  6. `test_full_seal_complete_commit_lifecycle_audit_flow`: 실제 `seal` -> `complete` -> git commit -> `check_lifecycle_evidence(strict=True)` 전 과정 성공 검증.

---

## 2. 변경 대상 파일 목록 (Target Files)
1. `src/forgeflow/harness.py`: `_tree_files_at_commit`, `_find_verified_completion_relocation_paths`, `_candidate_disallowed_paths`, `lifecycle_complete`
2. `src/forgeflow/_version.py`: 버전 0.1.15 승격
3. `docs/spec/CHANGELOG.md` & `src/forgeflow/templates/spec/CHANGELOG.md`: 변경 이력 추가
4. `tests/test_candidate_seal.py`: 회귀 테스트 추가
5. `tasks/in-progress/v0.1.15-fix-post-seal-relocation-audit/**`: 거버넌스 산출물

---

## 3. 검증 전략 (Verification Strategy)
- Stage 2 진입 전 게이트키퍼 검증: `forgeflow check --stage 2`
- 단위 테스트 실행: `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"`
- 하네스 거버넌스 감사: `forgeflow check --all --strict`
- Gate 2 QA Sign-off 및 Gate 3 릴리즈 승인/밀봉 완결
