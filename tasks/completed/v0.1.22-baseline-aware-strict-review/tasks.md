# Tasks & Implementation Checklist: Baseline-Aware Strict Review for Gate 2

- **Release ID**: `v0.1.22-baseline-aware-strict-review`

---

## 1. 구현 태스크 분해 (Atomic Tasks)

- [x] **Task 1: SmellDetector 오탐 수정 및 Scope 추적**
  - [x] 1.1: `from __future__ import ...` 미사용 임포트 오탐 방지 로직 구현
  - [x] 1.2: `CodeSmell`에 `scope: str = ""` 필드 추가 및 `fingerprint()` 메서드 구현
  - [x] 1.3: `_ASTSmellVisitor`에 `_scope_stack` 도입 및 AST 클래스/함수 방문 시 스코프 스택 갱신 연동
  - [x] 1.4: 단위 테스트 `tests/test_smell_detector.py`에 future import 및 scope 검증 테스트 추가

- [x] **Task 2: ReviewScanner Git Baseline & Scope Hunk 탐색 엔진**
  - [x] 2.1: `ReviewScanner.verify_git_ref(repo_root, ref)` 구현 (유효한 git commit 객체 검증)
  - [x] 2.2: `ReviewScanner.get_file_at_ref(repo_root, ref, rel_path)` 구현
  - [x] 2.3: `ReviewScanner.get_modified_lines(repo_root, ref, rel_path)` 구현 (diff 기반 변경 라인 번호 추출)
  - [x] 2.4: `ReviewScanner.get_function_scopes_and_lines(source_code)` 구현 (AST 기반 라인-스코프 매핑)

- [x] **Task 3: ReviewEngine Baseline 비교 및 Strict 판정 분기**
  - [x] 3.1: `ReviewResult`에 `findings_baseline`, `candidate_sha`, `baseline_stats` 필드 추가
  - [x] 3.2: `ReviewEngine.run_review`에 `findings_baseline: Optional[str]` 매개변수 추가
  - [x] 3.3: Baseline smells 수집 및 candidate smells와의 구조적 fingerprint 매칭 로직 구현
  - [x] 3.4: Modified scopes 기반 기존 경고 재검토(`MODIFIED_SCOPE`) 분류 및 신규/재발 경고 감지 로직 구현
  - [x] 3.5: Strict 판정 분기: baseline 미지정 시 기존 동작 100% 보존, baseline 지정 시 신규/수정영역 경고만 차단
  - [x] 3.6: Markdown 및 JSON 리포트에 baseline 비교 결과 및 통계 테이블 렌더링 반영

- [x] **Task 4: CLI 옵션 연동 (`--findings-baseline`)**
  - [x] 4.1: `parse_forgeflow_args` 및 `parse_harness_args`의 `review` 파서에 `--findings-baseline` 인자 추가
  - [x] 4.2: `cli.py`에서 `ReviewEngine.run_review`로 `findings_baseline` 인자 전달 연동
  - [x] 4.3: `tests/test_cli.py` 및 `tests/test_reviewer.py`에 CLI 및 엔드투엔드 baseline 테스트 작성

- [x] **Task 5: 버전 승격 및 종합 검증**
  - [x] 5.1: `src/forgeflow/_version.py` 패치 버전 승격 (`0.1.22`)
  - [x] 5.2: 전체 단위/통합 테스트 100% 통과 확인 (`pytest`)
  - [x] 5.3: 하네스 감사 `forgeflow check --all --strict` 전수 🟢 ALL PASSED 확인
