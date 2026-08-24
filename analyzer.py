import ast
import re
from dataclasses import dataclass, field
from typing import Optional

MAX_FUNCTION_LINES  = 50
MAX_FUNCTION_PARAMS = 6
MAX_NESTING_DEPTH   = 4

SECRET_KEYWORDS = [
    "password", "passwd", "pwd", "secret", "api_key", "apikey",
    "token", "auth_token", "access_token", "private_key", "client_secret",
]

SECRET_VALUE_PATTERN = re.compile(r"^(?!.*\{)(?!<)[A-Za-z0-9+/=_\-]{8,}$")


@dataclass
class Finding:
    severity: str
    category: str
    line: Optional[int]
    message: str
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "severity":   self.severity,
            "category":   self.category,
            "line":       self.line,
            "message":    self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class StaticAnalysisResult:
    filepath: str
    source_code: str
    language: str = "python"
    syntax_error: Optional[str] = None
    total_lines: int = 0
    functions: list = field(default_factory=list)
    classes: list   = field(default_factory=list)
    imports: list   = field(default_factory=list)
    findings: list  = field(default_factory=list)

    @property
    def function_count(self) -> int:
        return len(self.functions)

    @property
    def class_count(self) -> int:
        return len(self.classes)


class StaticAnalyzer:
    """Uzantıya göre Python veya C/C++ analizörünü çalıştıran ana fabrika sınıfı."""

    def analyze(self, filepath: str) -> StaticAnalysisResult:
        source_code = self._read_file(filepath)
        ext = filepath.split(".")[-1].lower() if "." in filepath else ""

        if ext in ("c", "cpp", "cc", "cxx", "h", "hpp"):
            return CPPAnalyzer().analyze(filepath, source_code)
        else:
            return PythonAnalyzer().analyze(filepath, source_code)

    def _read_file(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


class PythonAnalyzer:
    """Python AST tabanlı analizör."""

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="python")
        result.total_lines = len(source_code.splitlines())

        tree = self._parse(source_code, result)
        if result.syntax_error:
            return result

        visitor = _CodeVisitor(source_code)
        visitor.visit(tree)

        result.functions = visitor.functions
        result.classes   = visitor.classes
        result.imports   = visitor.imports
        result.findings  = visitor.findings

        self._check_hardcoded_secrets_regex(source_code, result)
        return result

    def _parse(self, source_code: str, result: StaticAnalysisResult):
        try:
            return ast.parse(source_code)
        except SyntaxError as e:
            result.syntax_error = f"Line {e.lineno}: {e.msg}"
            result.findings.append(Finding(
                severity="HIGH",
                category="Syntax",
                line=e.lineno,
                message=f"Syntax hatası: {e.msg}",
                suggestion="Kodu düzelterek tekrar çalıştırın.",
            ))
            return None

    def _check_hardcoded_secrets_regex(self, source_code: str, result: StaticAnalysisResult):
        lines = source_code.splitlines()
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for keyword in SECRET_KEYWORDS:
                pattern = re.compile(
                    rf'\b{re.escape(keyword)}\b\s*=\s*["\']([^"\']+)["\']',
                    re.IGNORECASE,
                )
                match = pattern.search(stripped)
                if match:
                    value = match.group(1)
                    if SECRET_VALUE_PATTERN.match(value):
                        already = any(
                            f.line == lineno and "hard-coded" in f.message.lower()
                            for f in result.findings
                        )
                        if not already:
                            result.findings.append(Finding(
                                severity="HIGH",
                                category="Security",
                                line=lineno,
                                message=f"Hard-coded '{keyword}' değeri tespit edildi.",
                                suggestion="Hassas değerleri .env dosyasına veya environment variable'a taşıyın.",
                            ))


class CPPAnalyzer:
    """C / C++ için statik kod analizörü (Regex ve desen taraması)."""

    UNSAFE_FUNCTIONS = {
        "strcpy": ("HIGH", "Buffer Overflow riski: 'strcpy' sınır kontrolü yapmaz.", "'strncpy' veya std::string kullanın."),
        "strcat": ("HIGH", "Buffer Overflow riski: 'strcat' sınır kontrolü yapmaz.", "'strncat' veya std::string kullanın."),
        "gets": ("HIGH", "Kritik Güvenlik Riski: 'gets' kullanımı sınırsız bellek yazımına neden olur.", "'fgets' veya std::cin kullanın."),
        "sprintf": ("MEDIUM", "Potansiyel Buffer Overflow: 'sprintf' boyutu denetlemez.", "'snprintf' veya std::ostringstream kullanın."),
        "system": ("HIGH", "Kabuk Enjeksiyonu Riski: 'system()' harici komut çalıştırır.", "Platforma özel güvenli API'ler veya execve kullanın."),
    }

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="cpp")
        lines = source_code.splitlines()
        result.total_lines = len(lines)

        self._extract_cpp_structures(lines, result)
        self._check_unsafe_functions(lines, result)
        self._check_dangerous_patterns(lines, result)
        self._check_secrets(lines, result)

        return result

    def _extract_cpp_structures(self, lines: list, result: StaticAnalysisResult):
        # Includes
        for line in lines:
            inc_match = re.match(r'^\s*#include\s+[<"]([^>"]+)[>"]', line)
            if inc_match:
                result.imports.append(inc_match.group(1))

        # Classes & Structs
        for idx, line in enumerate(lines, start=1):
            cls_match = re.search(r'\b(class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if cls_match and not line.strip().startswith("//"):
                result.classes.append({"name": cls_match.group(2), "line": idx})

        # Functions
        func_regex = re.compile(
            r'^(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{'
        )
        for idx, line in enumerate(lines, start=1):
            if line.strip().startswith("//") or line.strip().startswith("#"):
                continue
            match = func_regex.search(line)
            if match:
                name = match.group(1)
                if name not in ("if", "while", "for", "switch", "catch"):
                    params = [p.strip() for p in match.group(2).split(",") if p.strip()]
                    result.functions.append({
                        "name": name,
                        "line": idx,
                        "param_count": len(params),
                        "length": 0
                    })

    def _check_unsafe_functions(self, lines: list, result: StaticAnalysisResult):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            for func, (sev, msg, sug) in self.UNSAFE_FUNCTIONS.items():
                if re.search(rf'\b{func}\s*\(', stripped):
                    result.findings.append(Finding(
                        severity=sev,
                        category="Security",
                        line=idx,
                        message=msg,
                        suggestion=sug
                    ))

    def _check_dangerous_patterns(self, lines: list, result: StaticAnalysisResult):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue

            # Format String Vulnerability (örn: printf(str);)
            if re.search(r'\bprintf\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)\s*;', stripped):
                result.findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=idx,
                    message="Format String Açığı: 'printf' doğrudan değişkene paslanmış.",
                    suggestion="Format belirteci kullanın: printf(\"%s\", var);"
                ))

            # Malloc without NULL check or Raw Pointer Memory Leak risk
            if re.search(r'\b(malloc|calloc|realloc)\s*\(', stripped):
                result.findings.append(Finding(
                    severity="MEDIUM",
                    category="Memory Safety",
                    line=idx,
                    message="Dinamik bellek tahsisi: NULL kontrolü ve free() unutulmamalıdır.",
                    suggestion="C++ yazıyorsanız RAII ve std::unique_ptr / std::make_unique tercih edin."
                ))

    def _check_secrets(self, lines: list, result: StaticAnalysisResult):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            for kw in SECRET_KEYWORDS:
                pattern = re.compile(rf'{kw}\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
                match = pattern.search(stripped)
                if match and SECRET_VALUE_PATTERN.match(match.group(1)):
                    result.findings.append(Finding(
                        severity="HIGH",
                        category="Security",
                        line=idx,
                        message=f"Hard-coded C/C++ '{kw}' değeri tespit edildi.",
                        suggestion="Hassas değerleri ortam değişkenlerinden veya güvenli bir yapılandırma dosyasından okuyun."
                    ))


class _CodeVisitor(ast.NodeVisitor):
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.functions: list = []
        self.classes: list   = []
        self.imports: list   = []
        self.findings: list  = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.append({"name": node.name, "line": node.lineno})
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        self._check_dangerous_call(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.findings.append(Finding(
                severity="MEDIUM",
                category="Code Quality",
                line=node.lineno,
                message="Çıplak 'except:' kullanımı — tüm exception'lar yakalanıyor.",
                suggestion="Beklenen exception tipini açıkça belirtin: except ValueError: gibi.",
            ))
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            self.findings.append(Finding(
                severity="LOW",
                category="Code Quality",
                line=node.lineno,
                message="Çok genel 'except Exception:' kullanımı.",
                suggestion="Daha spesifik exception tipleri kullanmayı tercih edin.",
            ))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        self._check_hardcoded_secret_assignment(node)
        self.generic_visit(node)

    def _analyze_function(self, node):
        start_line  = node.lineno
        end_line    = getattr(node, "end_lineno", None) or self._estimate_end_line(node)
        length      = (end_line - start_line + 1) if end_line else 0
        args        = node.args
        param_count = (
            len(args.args)
            + len(args.posonlyargs)
            + len(args.kwonlyargs)
            + (1 if args.vararg else 0)
            + (1 if args.kwarg else 0)
        )

        self.functions.append({
            "name":        node.name,
            "line":        start_line,
            "param_count": param_count,
            "length":      length,
        })

        if length > MAX_FUNCTION_LINES:
            self.findings.append(Finding(
                severity="MEDIUM",
                category="Code Quality",
                line=start_line,
                message=f"Fonksiyon '{node.name}' çok uzun ({length} satır, eşik: {MAX_FUNCTION_LINES}).",
                suggestion="Fonksiyonu daha küçük, tek sorumluluğu olan parçalara bölün.",
            ))

        if param_count > MAX_FUNCTION_PARAMS:
            self.findings.append(Finding(
                severity="LOW",
                category="Code Quality",
                line=start_line,
                message=f"Fonksiyon '{node.name}' çok fazla parametre alıyor ({param_count}, eşik: {MAX_FUNCTION_PARAMS}).",
                suggestion="Parametreleri bir dataclass veya dict'e taşıyarak API'yi basitleştirin.",
            ))

        max_depth = _NestingDepthCalculator().calculate(node)
        if max_depth > MAX_NESTING_DEPTH:
            self.findings.append(Finding(
                severity="MEDIUM",
                category="Complexity",
                line=start_line,
                message=f"Fonksiyon '{node.name}' aşırı iç içe geçmiş kod içeriyor (derinlik: {max_depth}).",
                suggestion="Early return / guard clause kullanarak iç içe geçmeyi azaltın.",
            ))

    def _check_dangerous_call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            self.findings.append(Finding(
                severity="HIGH",
                category="Security",
                line=node.lineno,
                message=f"Tehlikeli fonksiyon '{node.func.id}()' kullanımı.",
                suggestion=f"'{node.func.id}()' kullanımından kaçının; güvenlik açığı oluşturabilir.",
            ))

        func_str = self._get_call_name(node)
        if func_str and "subprocess" in func_str:
            for kw in node.keywords:
                if (
                    kw.arg == "shell"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True
                ):
                    self.findings.append(Finding(
                        severity="HIGH",
                        category="Security",
                        line=node.lineno,
                        message="subprocess çağrısında 'shell=True' kullanımı.",
                        suggestion="Argümanları liste olarak geçirin: subprocess.run(['cmd', 'arg1'])",
                    ))

        if func_str in ("os.system", "os.popen"):
            self.findings.append(Finding(
                severity="MEDIUM",
                category="Security",
                line=node.lineno,
                message=f"'{func_str}()' kabuk enjeksiyonuna açık olabilir.",
                suggestion="subprocess modülünü shell=False ile kullanın.",
            ))

    def _check_hardcoded_secret_assignment(self, node: ast.Assign):
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            var_lower = target.id.lower()
            for keyword in SECRET_KEYWORDS:
                if keyword in var_lower:
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        val = node.value.value
                        if val and SECRET_VALUE_PATTERN.match(val):
                            self.findings.append(Finding(
                                severity="HIGH",
                                category="Security",
                                line=node.lineno,
                                message=f"Hard-coded '{keyword}' değeri tespit edildi: '{target.id}'.",
                                suggestion="Hassas değerleri .env dosyasına veya environment variable'a taşıyın.",
                            ))

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            parts, current = [], node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None

    def _estimate_end_line(self, node) -> int:
        max_line = node.lineno
        for child in ast.walk(node):
            if hasattr(child, "lineno"):
                max_line = max(max_line, child.lineno)
        return max_line


class _NestingDepthCalculator(ast.NodeVisitor):
    def __init__(self):
        self._current = 0
        self._max = 0

    def calculate(self, func_node) -> int:
        self.visit(func_node)
        return self._max

    def _enter(self, node):
        self._current += 1
        self._max = max(self._max, self._current)
        self.generic_visit(node)
        self._current -= 1

    def visit_For(self, node):       self._enter(node)
    def visit_While(self, node):     self._enter(node)
    def visit_If(self, node):        self._enter(node)
    def visit_With(self, node):      self._enter(node)
    def visit_Try(self, node):       self._enter(node)
    def visit_AsyncFor(self, node):  self._enter(node)
    def visit_AsyncWith(self, node): self._enter(node)
