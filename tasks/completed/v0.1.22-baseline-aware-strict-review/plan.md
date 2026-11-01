# Architecture & Technical Plan: Baseline-Aware Strict Review for Gate 2

- **Release ID**: `v0.1.22-baseline-aware-strict-review`
- **Target Component**: `src/forgeflow/_version.py`, `src/forgeflow/smell_detector.py`, `src/forgeflow/reviewer.py`, `src/forgeflow/review_scanner.py`, `src/forgeflow/cli.py`, `src/forgeflow/report_renderer.py`

---

## 1. 아키텍처 개요 (Architectural Overview)

```text
[CLI / harness review]
   │  --strict --findings-baseline <ref>
   ▼
[ReviewEngine.run_review]
   ├── 1. ReviewScanner.verify_git_ref(ref) ──> 유효성 검증 (Fail-Closed)
   ├── 2. SmellDetector.analyze_code (Candidate files) ──> candidate_smells (with scope)
   ├── 3. ReviewScanner.get_file_at_ref(ref, path) ──> baseline_smells (with scope)
   ├── 4. ReviewScanner.get_modified_lines(ref, path) ──> diff_hunks & modified_scopes
   └── 5. BaselineComparator.compare(candidate, baseline, modified_scopes)
            ├── critical_smells (무조건 차단)
            ├── new_smells (기준선에 없음 ➔ 차단)
            ├── modified_scope_smells (수정된 함수 내 기존 경고 ➔ 차단/재검토)
            ├── baseline_existing_smells (수정되지 않은 함수 내 기존 경고 ➔ 면제/표시)
            └── resolved_smells (기준선에 있었으나 해소됨 ➔ 집계)
```

---

## 2. 데이터 모델 및 인터페이스 (Data Models & Interfaces)

### 2.1 CodeSmell 확장
```python
@dataclass
class CodeSmell:
    file_path: str
    line_no: int
    smell_type: str
    severity: str  # CRITICAL, WARNING, INFO
    message: str
    suggestion: str
    scope: str = ""  # e.g., "ClassName.method_name", "function_name", or ""

    def fingerprint(self, rel_path: str) -> str:
        # 줄 번호에 영향받지 않는 구조적 식별자
        return f"{rel_path}:{self.smell_type}:{self.scope}:{self._message_key()}"
```

### 2.2 ReviewResult 확장
```python
@dataclass
class ReviewResult:
    repo_root: str
    target_scope: str
    files_scanned: List[str]
    smells: List[CodeSmell]
    ...
    passed: bool
    strict: bool
    findings_baseline: Optional[str] = None
    candidate_sha: Optional[str] = None
    baseline_stats: Optional[Dict[str, int]] = None
    # {
    #   "baseline_warnings": int,
    #   "new_warnings": int,
    #   "modified_scope_warnings": int,
    #   "resolved_warnings": int,
    #   "exempt_warnings": int,
    # }
```

---

## 3. 핵심 알고리즘 설계 (Key Algorithms)

### 3.1 Unused Import 오탐 교정
- `SmellDetector.visit_ImportFrom`에서 `node.module == "__future__"`인 경우 `self._imports`에 등록하지 않음.

### 3.2 AST Scope 추적
- `_ASTSmellVisitor`에 `_scope_stack: List[str]` 유지.
- `visit_ClassDef`: `_scope_stack.append(node.name)` ➔ generic_visit ➔ `_scope_stack.pop()`
- `visit_FunctionDef` / `visit_AsyncFunctionDef`: `_scope_stack.append(node.name)` ➔ generic_visit ➔ `_scope_stack.pop()`
- `_add_smell`: `scope = ".".join(self._scope_stack)`

### 3.3 Diff Hunks 기반 Modified Scope 산출
- `git diff -U0 <ref>...HEAD -- <path>` (또는 working tree 대상)에서 변경된 라인 번호 추출.
- AST 파싱 결과 각 함수/메서드의 `(lineno, end_lineno, scope_name)` 범위를 구하고, 변경된 라인이 포함된 함수 스코프 집합(`modified_scopes`) 산출.
- 기준선 경고 중 해당 파일의 `modified_scopes`에 속한 경고는 `modified_scope_smells`로 분류.

### 3.4 Strict 판정 규칙
- `strict`가 활성화된 경우:
  - `findings_baseline` 미지정: `effective_critical == 0 and total_warning == 0` (기존 동작 100% 동일).
  - `findings_baseline` 지정: `effective_critical == 0 and new_warnings == 0 and modified_scope_warnings == 0`. (무관한 기존 경고 `exempt_warnings`는 통과 허용).
