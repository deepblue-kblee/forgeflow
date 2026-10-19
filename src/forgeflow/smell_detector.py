"""
AST-based Code Smell and Quality Metrics Detector (Zero-Dependency)
"""

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

IDIOMATIC_NAMES = {"_", "i", "j", "k", "n", "e", "ex", "f", "v", "x", "y", "z", "fp", "db", "id", "r", "w", "cb", "ts", "p"}
VAGUE_IDENTIFIERS = {"data", "info", "temp", "tmp", "foo", "bar", "baz", "thing", "stuff", "obj", "item"}
PYTHON_BUILTINS = {
    "id", "type", "list", "dict", "str", "int", "len", "open", "all", "any",
    "input", "format", "dir", "filter", "map", "max", "min", "sum", "range",
    "set", "tuple", "bytes", "iter", "next", "hash", "super", "object",
}


@dataclass
class CodeSmell:
    file_path: str
    line_no: int
    smell_type: str
    severity: str  # CRITICAL, WARNING, INFO
    message: str
    suggestion: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_cognitive_complexity(func_node: ast.AST, func_name: Optional[str] = None) -> int:
    """Calculate Cognitive Complexity for a function/method AST node using the SonarSource model."""
    if func_name is None and hasattr(func_node, "name"):
        func_name = getattr(func_node, "name")

    score = 0

    def _traverse(node: ast.AST, nesting: int, is_elif: bool = False):
        nonlocal score

        if isinstance(node, ast.If):
            if is_elif:
                score += 1
            else:
                score += 1 + nesting

            _traverse_expr(node.test, nesting)
            for stmt in node.body:
                _traverse(stmt, nesting + 1)

            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                _traverse(node.orelse[0], nesting, is_elif=True)
            elif node.orelse:
                score += 1
                for stmt in node.orelse:
                    _traverse(stmt, nesting + 1)
            return

        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            score += 1 + nesting
            if hasattr(node, "test"):
                _traverse_expr(node.test, nesting)
            for stmt in node.body:
                _traverse(stmt, nesting + 1)
            for stmt in node.orelse:
                _traverse(stmt, nesting + 1)
            return

        elif isinstance(node, ast.ExceptHandler):
            score += 1 + nesting
            for stmt in node.body:
                _traverse(stmt, nesting + 1)
            return

        elif hasattr(ast, "Match") and isinstance(node, getattr(ast, "Match")):
            score += 1 + nesting
            _traverse_expr(node.subject, nesting)
            for case in node.cases:
                if getattr(case, "guard", None):
                    _traverse_expr(case.guard, nesting + 1)
                for stmt in case.body:
                    _traverse(stmt, nesting + 1)
            return

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            score += 1 + nesting
            for stmt in node.body:
                _traverse(stmt, nesting + 1)
            return

        for child in ast.iter_child_nodes(node):
            _traverse_expr(child, nesting)

    def _traverse_expr(node: ast.AST, nesting: int):
        nonlocal score
        if isinstance(node, ast.IfExp):
            score += 1 + nesting
            _traverse_expr(node.test, nesting + 1)
            _traverse_expr(node.body, nesting + 1)
            _traverse_expr(node.orelse, nesting + 1)
            return
        elif isinstance(node, ast.BoolOp):
            score += max(0, len(node.values) - 1)
            for val in node.values:
                _traverse_expr(val, nesting)
            return
        elif isinstance(node, ast.Call):
            call_id = None
            if isinstance(node.func, ast.Name):
                call_id = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_id = node.func.attr
            if func_name and call_id == func_name:
                score += 1
        elif isinstance(node, ast.Lambda):
            for child in ast.iter_child_nodes(node):
                _traverse_expr(child, nesting + 1)
            return

        for child in ast.iter_child_nodes(node):
            _traverse(child, nesting)

    if hasattr(func_node, "body") and isinstance(func_node.body, list):
        for stmt in func_node.body:
            _traverse(stmt, 0)

    return score


class _ASTSmellVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.smells: List[CodeSmell] = []
        self._current_nesting = 0
        self._loop_depth = 0
        self._current_class_methods = 0
        self._scope_depth = 0
        self._in_main_block = False
        self._with_depth = 0
        self._imported_modules: Set[str] = set()
        self._imports: Dict[str, int] = {}
        self._referenced_names: Set[str] = set()
        self._exported_names: Set[str] = set()

    def _add_smell(self, node: ast.AST, smell_type: str, severity: str, message: str, suggestion: str):
        line = getattr(node, "lineno", 1)
        self.smells.append(
            CodeSmell(
                file_path=self.file_path,
                line_no=line,
                smell_type=smell_type,
                severity=severity,
                message=message,
                suggestion=suggestion,
            )
        )

    def visit_Module(self, node: ast.Module):
        line_count = len(self.source_lines)
        if line_count > 800:
            self._add_smell(
                node,
                smell_type="File Bloat",
                severity="CRITICAL",
                message=f"파일의 전체 줄 수가 {line_count}줄로 기준(800줄)을 초과하여 God Module 위험이 있습니다.",
                suggestion="패키지 디렉터리로 승격(Package Promotion)하거나 하위 도메인별 모듈로 역할을 분리하세요.",
            )
        elif line_count > 500:
            self._add_smell(
                node,
                smell_type="File Bloat",
                severity="WARNING",
                message=f"파일의 전체 줄 수가 {line_count}줄로 권고 기준(500줄)을 초과합니다.",
                suggestion="단일 책임 원칙(SRP)을 검토하고 응집된 하위 모듈로 책임을 분리하세요.",
            )

        self.generic_visit(node)

        # Post-traversal module-level inspections
        # 1. Excessive Imports Check (> 20 external/top-level imported modules)
        if len(self._imported_modules) > 20:
            self._add_smell(
                node,
                smell_type="Excessive Imports",
                severity="WARNING",
                message=f"모듈에서 임포트하는 외부 의존성이 {len(self._imported_modules)}개로 기준(20개)을 초과하여 결합도가 높습니다.",
                suggestion="단일 책임 원칙(SRP)을 검토하고 응집된 하위 모듈로 책임을 분리하세요.",
            )

        # 2. Unused Import Check
        for imported_name, lineno in self._imports.items():
            if (
                imported_name not in self._referenced_names
                and imported_name not in self._exported_names
                and not imported_name.startswith("_")
            ):
                dummy_node = ast.Name(id=imported_name, ctx=ast.Load())
                dummy_node.lineno = lineno
                self._add_smell(
                    dummy_node,
                    smell_type="Unused Import",
                    severity="WARNING",
                    message=f"임포트된 식별자 '{imported_name}'이 모듈 내부에서 한 번도 사용되지 않았습니다.",
                    suggestion="불필요한 임포트를 제거하여 코드 위생과 로딩 성능을 개선하세요.",
                )

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            mod = alias.name.split(".")[0]
            self._imported_modules.add(mod)
            if self._scope_depth == 0:
                self._imports[alias.asname or alias.name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            mod = node.module.split(".")[0]
            self._imported_modules.add(mod)
        if self._scope_depth == 0:
            for alias in node.names:
                if alias.name != "*":
                    self._imports[alias.asname or alias.name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self._referenced_names.add(node.id)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # 1. Detect __all__ export bindings
        if self._scope_depth == 0:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                self._exported_names.add(elt.value)

        # 2. Builtin Shadowing on local variable assignments
        if self._scope_depth > 0:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if (
                        target.id in PYTHON_BUILTINS
                        and not target.id.startswith("_")
                        and target.id not in ("self", "cls")
                    ):
                        self._add_smell(
                            target,
                            smell_type="Builtin Shadowing",
                            severity="WARNING",
                            message=f"로컬 변수명 '{target.id}'이 파이썬 내장 빌트인 식별자를 덮어씁니다(Shadowing).",
                            suggestion="도메인 의도를 드러내는 명확한 대체 이름으로 변경하세요.",
                        )

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if self._scope_depth > 0 and isinstance(node.target, ast.Name):
            if (
                node.target.id in PYTHON_BUILTINS
                and not node.target.id.startswith("_")
                and node.target.id not in ("self", "cls")
            ):
                self._add_smell(
                    node.target,
                    smell_type="Builtin Shadowing",
                    severity="WARNING",
                    message=f"로컬 변수명 '{node.target.id}'이 파이썬 내장 빌트인 식별자를 덮어씁니다(Shadowing).",
                    suggestion="도메인 의도를 드러내는 명확한 대체 이름으로 변경하세요.",
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._scope_depth += 1
        self._check_function(node)
        self.generic_visit(node)
        self._scope_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._scope_depth += 1
        self._check_function(node)
        self.generic_visit(node)
        self._scope_depth -= 1

    def visit_With(self, node: ast.With):
        self._with_depth += 1
        self.generic_visit(node)
        self._with_depth -= 1

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self._with_depth += 1
        self.generic_visit(node)
        self._with_depth -= 1

    def _is_main_guard(self, node: ast.If) -> bool:
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__":
                for comp in node.test.comparators:
                    if isinstance(comp, ast.Constant) and comp.value == "__main__":
                        return True
        return False

    def visit_Call(self, node: ast.Call):
        func_name = self._get_call_name(node.func)

        # 1. Top-level Side-Effect Check
        if self._scope_depth == 0 and not self._in_main_block:
            side_effect_calls = {
                "logging.basicConfig",
                "addHandler",
                "sqlite3.connect",
                "open",
                "urlopen",
                "urllib.request.urlopen",
                "socket.socket",
                "subprocess.Popen",
                "subprocess.run",
                "subprocess.check_output",
                "threading.Thread",
                "asyncio.create_task",
                "aiohttp.ClientSession",
            }
            if func_name in side_effect_calls or func_name.endswith(".addHandler"):
                self._add_smell(
                    node,
                    smell_type="Top-level Side-Effect",
                    severity="CRITICAL",
                    message=f"모듈 최상위 스코프에서 자원 획득/로거 핸들러 등록 호출('{func_name}')이 실행되어 import 시 부수효과 및 자원 누수가 발생합니다.",
                    suggestion="자원 획득 로직을 명시적 초기화 함수(예: setup_logging(), connect_db())나 'if __name__ == \"__main__\":' 블록 내부로 이동하세요.",
                )

        # 2. Unmanaged Resource Allocation Check
        unmanaged_resources = {"open", "sqlite3.connect", "aiohttp.ClientSession", "socket.socket"}
        if func_name in unmanaged_resources and self._with_depth == 0 and not self._in_main_block:
            self._add_smell(
                node,
                smell_type="Unmanaged Resource",
                severity="WARNING",
                message=f"자원 획득 호출('{func_name}')이 'with' 컨텍스트 매니저 없이 사용되어 예외 발생 시 자원 누수 위험이 있습니다.",
                suggestion=f"RAII 원칙에 따라 'with {func_name}(...) as ...:' 구문을 사용하여 자동 해제되도록 감싸세요.",
            )

        # 3. Security Vulnerability Checks
        # Subprocess with shell=True
        if func_name in (
            "subprocess.run", "subprocess.Popen", "subprocess.call",
            "subprocess.check_output", "subprocess.check_call"
        ) or func_name.endswith((".run", ".Popen", ".call", ".check_output", ".check_call")):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._add_smell(
                        node,
                        smell_type="Security Vulnerability",
                        severity="CRITICAL",
                        message="'subprocess' 호출에서 'shell=True'가 사용되어 명령어 삽입(Command Injection) 공격에 취약합니다.",
                        suggestion="'shell=True'를 제거하고 인자를 리스트(List[str]) 형태로 안전하게 분리하여 전달하세요.",
                    )

        # eval / exec calls
        if func_name in ("eval", "exec"):
            self._add_smell(
                node,
                smell_type="Security Vulnerability",
                severity="CRITICAL",
                message=f"동적 코드 실행 함수('{func_name}')가 호출되어 코드 주입 공격 위험이 있습니다.",
                suggestion="'ast.literal_eval'이나 정적 매핑 딕셔너리로 대체하세요.",
            )

        # Insecure tempfile.mktemp
        if func_name in ("tempfile.mktemp", "mktemp") or func_name.endswith(".mktemp"):
            self._add_smell(
                node,
                smell_type="Security Vulnerability",
                severity="CRITICAL",
                message="'tempfile.mktemp()'는 경쟁 상태(Race Condition) 취약점이 있는 보안 폐기 대상 함수입니다.",
                suggestion="'tempfile.NamedTemporaryFile()' 또는 'tempfile.mkstemp()'를 사용하세요.",
            )

        # 4. Multi-Axis Metric: I/O in Loop Check
        if self._loop_depth > 0:
            io_funcs = {"open", "read_text", "read_bytes", "write_text", "write_bytes"}
            if func_name in io_funcs or any(func_name.endswith(f".{f}") for f in ("read_text", "read_bytes", "write_text", "write_bytes")):
                self._add_smell(
                    node,
                    smell_type="I/O in Loop",
                    severity="WARNING",
                    message=f"루프 내부에서 반복적인 디스크 I/O 함수('{func_name}')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.",
                    suggestion="루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.",
                )

        self.generic_visit(node)

    def _get_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._get_call_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        return ""

    def _check_function(self, node: Any):
        # 1. Long Function
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)
        line_count = end_line - start_line + 1
        if line_count > 50:
            self._add_smell(
                node,
                smell_type="Long Function",
                severity="WARNING",
                message=f"함수 '{node.name}'의 길이가 {line_count}줄로 기준(50줄)을 초과합니다.",
                suggestion="함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.",
            )

        # 2. Too Many Parameters (Data Clumps)
        total_args = len(node.args.args) + len(node.args.kwonlyargs)
        if node.args.args and node.args.args[0].arg in ("self", "cls"):
            total_args -= 1

        if total_args > 5:
            self._add_smell(
                node,
                smell_type="Too Many Parameters",
                severity="WARNING",
                message=f"함수 '{node.name}'의 매개변수가 {total_args}개로 기준(5개)을 초과합니다.",
                suggestion="매개변수를 하나의 DTO/Dataclass 객체로 묶어 전달하는 것을 고려하세요.",
            )

        # 3. Mysterious Name
        if not node.name.startswith("_"):
            if len(node.name) == 1 and node.name not in IDIOMATIC_NAMES:
                self._add_smell(
                    node,
                    smell_type="Mysterious Name",
                    severity="WARNING",
                    message=f"함수명 '{node.name}'이 모호하거나 너무 짧습니다.",
                    suggestion="역할과 동작을 명확히 드러내는 이름으로 변경하세요.",
                )
            elif node.name.lower() in VAGUE_IDENTIFIERS:
                self._add_smell(
                    node,
                    smell_type="Mysterious Name",
                    severity="INFO",
                    message=f"함수명 '{node.name}'이 다소 추상적입니다.",
                    suggestion="구체적인 도메인 의도를 담은 이름으로 구체화하세요.",
                )

        # 4. Builtin Shadowing on function parameters
        for arg in node.args.args + node.args.kwonlyargs:
            if arg.arg in ("self", "cls") or arg.arg.startswith("_"):
                continue
            if arg.arg in PYTHON_BUILTINS:
                self._add_smell(
                    arg,
                    smell_type="Builtin Shadowing",
                    severity="WARNING",
                    message=f"함수 매개변수명 '{arg.arg}'이 파이썬 내장 빌트인 식별자를 덮어씁니다(Shadowing).",
                    suggestion="도메인 의도를 드러내는 명확한 대체 이름으로 변경하세요.",
                )

        # 5. Missing Type Annotations (for public functions)
        if not node.name.startswith("_"):
            untyped_args = []
            for arg in node.args.args:
                if arg.arg in ("self", "cls"):
                    continue
                if arg.annotation is None:
                    untyped_args.append(arg.arg)
            if untyped_args or node.returns is None:
                details = []
                if untyped_args:
                    details.append(f"인자 타입 누락: {', '.join(untyped_args)}")
                if node.returns is None:
                    details.append("반환 타입 누락")
                self._add_smell(
                    node,
                    smell_type="Missing Type Annotations",
                    severity="INFO",
                    message=f"공용 함수 '{node.name}'의 타입 힌트가 누락되었습니다 ({'; '.join(details)}).",
                    suggestion="정적 타입 안정성을 위해 인자 및 반환값에 Type Annotation을 추가하세요.",
                )

        # 6. High Cognitive Complexity
        cog_score = calculate_cognitive_complexity(node, func_name=node.name)
        if cog_score > 15:
            self._add_smell(
                node,
                smell_type="High Cognitive Complexity",
                severity="WARNING",
                message=f"함수 '{node.name}'의 인지 복잡도(Cognitive Complexity)가 {cog_score}점으로 기준(15점)을 초과합니다.",
                suggestion="중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.",
            )

    def visit_ClassDef(self, node: ast.ClassDef):
        # Class size check
        method_count = sum(
            1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        if method_count > 15:
            self._add_smell(
                node,
                smell_type="Large Class",
                severity="WARNING",
                message=f"클래스 '{node.name}'의 메서드가 {method_count}개로 지나치게 많습니다.",
                suggestion="클래스의 책임을 단일화하고 일부 역할을 컴포지션으로 분리하세요.",
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # 1. Bare Except Check
        if node.type is None:
            self._add_smell(
                node,
                smell_type="Bare Except",
                severity="CRITICAL",
                message="'except:' 절에서 예외 타입을 지정하지 않아 모든 예외(KeyboardInterrupt 등)를 무차별 포획합니다.",
                suggestion="구체적인 Exception 타입(예: Exception, ValueError 등)을 명시하세요.",
            )
        elif isinstance(node.type, ast.Name) and node.type.id == "BaseException":
            self._add_smell(
                node,
                smell_type="Bare Except",
                severity="CRITICAL",
                message="'except BaseException:'을 사용하여 시스템 종료 신호까지 가로챌 위험이 있습니다.",
                suggestion="'except Exception:' 또는 더 구체적인 예외 클래스를 지정하세요.",
            )
        else:
            # 2. Silent Exception Check (empty body with only 'pass' or '...')
            is_silent = False
            if len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Pass):
                    is_silent = True
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    if stmt.value.value is Ellipsis or stmt.value.value is ...:
                        is_silent = True

            if is_silent:
                self._add_smell(
                    node,
                    smell_type="Silent Exception",
                    severity="WARNING",
                    message="'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.",
                    suggestion="적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.",
                )

        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        is_main = self._is_main_guard(node)
        prev_main = self._in_main_block
        if is_main:
            self._in_main_block = True
        self._check_nesting(node)
        self._in_main_block = prev_main

    def visit_For(self, node: ast.For):
        self._loop_depth += 1
        self._check_nesting(node)
        self._loop_depth -= 1

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._loop_depth += 1
        self._check_nesting(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While):
        self._loop_depth += 1
        self._check_nesting(node)
        self._loop_depth -= 1

    def visit_Try(self, node: ast.Try):
        self._check_nesting(node)

    def _check_nesting(self, node: ast.AST):
        self._current_nesting += 1
        if self._current_nesting >= 4:
            self._add_smell(
                node,
                smell_type="Deep Nesting",
                severity="WARNING",
                message=f"코드 블록의 중첩 깊이가 {self._current_nesting}단계로 가독성이 저하됩니다.",
                suggestion="Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.",
            )
        self.generic_visit(node)
        self._current_nesting -= 1


class SmellDetector:
    """Zero-Dependency AST-based Code Smell and Quality Analyzer."""

    @classmethod
    def analyze_code(cls, code: str, file_path: str = "<string>") -> List[CodeSmell]:
        if not code.strip():
            return []
        try:
            tree = ast.parse(code, filename=file_path)
        except SyntaxError as e:
            return [
                CodeSmell(
                    file_path=file_path,
                    line_no=e.lineno or 1,
                    smell_type="Syntax Error",
                    severity="CRITICAL",
                    message=f"파이썬 구문 오류: {e.msg}",
                    suggestion="구문 오류를 수정하여 유효한 파이썬 코드를 작성하세요.",
                )
            ]

        visitor = _ASTSmellVisitor(file_path=file_path, source_lines=code.splitlines())
        visitor.visit(tree)
        return visitor.smells

    @classmethod
    def analyze_file(cls, file_path: Path) -> List[CodeSmell]:
        try:
            content = file_path.read_text(encoding="utf-8")
            return cls.analyze_code(content, file_path=str(file_path))
        except UnicodeDecodeError as exc:
            return [
                CodeSmell(
                    file_path=str(file_path),
                    line_no=1,
                    smell_type="Encoding Error",
                    severity="CRITICAL",
                    message=f"파일 인코딩 오류(UTF-8 디코딩 실패): {exc}",
                    suggestion="파일을 유효한 UTF-8 인코딩으로 저장하세요.",
                )
            ]
        except Exception as e:
            return [
                CodeSmell(
                    file_path=str(file_path),
                    line_no=1,
                    smell_type="Read Error",
                    severity="WARNING",
                    message=f"파일 분석 실패: {str(e)}",
                    suggestion="파일 인코딩 및 권한을 확인하세요.",
                )
            ]
