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

# Minimum 12 karakter, sadece sayıdan oluşan değerleri de dışla
SECRET_VALUE_PATTERN = re.compile(r"^(?!.*\{)(?!<)(?!\d+$)[A-Za-z0-9+/=_\-]{12,}$")

PLACEHOLDER_VALUES = {
    "changeme", "change_me", "yourkey", "your_key", "your_key_here",
    "example", "placeholder", "xxxx", "xxxxxxxx", "test", "testing",
    "password", "secret", "admin", "root", "pass", "none", "null",
    "12345678", "123456789", "abcdefgh", "todo", "fixme", "replace_me",
    "insert_key_here", "enter_key_here", "add_key_here", "your_secret",
    "your_token", "your_api_key", "put_your_key_here",
}


def _is_suppressed(line: str) -> bool:
    """Satır # noreview veya // noreview içeriyorsa True döner."""
    low = line.lower()
    return "# noreview" in low or "// noreview" in low


def _postprocess_findings(findings: list, original_lines: list) -> list:
    """
    1. # noreview / // noreview etiketli satırları siler.
    2. Aynı (category, message) bilgisine sahip bulguları tek bir bulgu altında
       birleştirir ve satır numaralarını 'lines' listesinde toplar.
    """
    active = []
    for f in findings:
        if f.line is not None and f.line <= len(original_lines):
            if _is_suppressed(original_lines[f.line - 1]):
                continue
        active.append(f)

    grouped: dict = {}
    grouped_order: list = []

    for f in active:
        key = (f.category, f.message.strip(), f.severity)
        if key not in grouped:
            # Satır numaralarını benzersiz ve sıralı tut
            lines_set = [f.line] if f.line is not None else []
            f.lines = lines_set
            grouped[key] = f
            grouped_order.append(f)
        else:
            existing = grouped[key]
            if f.line is not None and f.line not in existing.lines:
                existing.lines.append(f.line)
                existing.lines.sort()

    return grouped_order


@dataclass
class Finding:
    severity: str
    category: str
    line: Optional[int]
    message: str
    suggestion: Optional[str] = None
    confidence: float = 1.0
    lines: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "severity":   self.severity,
            "category":   self.category,
            "line":       self.line,
            "lines":      self.lines if self.lines else ([self.line] if self.line is not None else []),
            "message":    self.message,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
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
    """Uzantıya göre Python, C/C++ veya Java analizörünü çalıştıran ana fabrika sınıfı."""

    def analyze(self, filepath: str) -> StaticAnalysisResult:
        source_code = self._read_file(filepath)
        ext = filepath.split(".")[-1].lower() if "." in filepath else ""

        if ext in ("c", "cpp", "cc", "cxx", "h", "hpp"):
            return CPPAnalyzer().analyze(filepath, source_code)
        elif ext == "java":
            return JavaAnalyzer().analyze(filepath, source_code)
        elif ext == "cs":
            return CSharpAnalyzer().analyze(filepath, source_code)
        elif ext == "css":
            return CSSAnalyzer().analyze(filepath, source_code)

        elif ext in ("html", "htm"):
            return HTMLAnalyzer().analyze(filepath, source_code)
        elif ext in ("js", "jsx", "ts", "tsx", "mjs"):
            return JSAnalyzer().analyze(filepath, source_code)
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
        result.findings = _postprocess_findings(result.findings, source_code.splitlines())
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
            if stripped.startswith("#") or _is_suppressed(line):
                continue
            for keyword in SECRET_KEYWORDS:
                pattern = re.compile(
                    rf'\b{re.escape(keyword)}\b\s*=\s*["\']([^"\']+)["\']',
                    re.IGNORECASE,
                )
                match = pattern.search(stripped)
                if match:
                    value = match.group(1)
                    if SECRET_VALUE_PATTERN.match(value) and value.lower() not in PLACEHOLDER_VALUES:
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
                                confidence=0.8,
                            ))


class CPPAnalyzer:
    """C / C++ için statik kod analizörü (Regex ve desen taraması)."""

    UNSAFE_FUNCTIONS = {
        "strcpy": ("HIGH", "Buffer Overflow riski: 'strcpy' sınır kontrolü yapmaz.", "'strncpy' veya std::string kullanın."),
        "strcat": ("HIGH", "Buffer Overflow riski: 'strcat' sınır kontrolü yapmaz.", "'strncat' veya std::string kullanın."),
        "gets": ("HIGH", "Kritik Güvenlik Riski: 'gets' kullanımı sınırsız bellek yazımına neden olur.", "'fgets' veya std::cin kullanın."),
        "sprintf": ("MEDIUM", "Potansiyel Buffer Overflow: 'sprintf' boyutu denetlemez.", "'snprintf' veya std::ostringstream kullanın."),
        "vsprintf": ("MEDIUM", "Potansiyel Buffer Overflow: 'vsprintf' boyutu denetlemez.", "'vsnprintf' kullanın."),
        "system": ("HIGH", "Kabuk Enjeksiyonu Riski: 'system()' harici komut çalıştırır.", "Platforma özel güvenli API'ler veya execve kullanın."),
        "strtok": ("LOW", "Thread-Safety riski: 'strtok' global durum kullanır.", "'strtok_r' veya std::string_view tercih edin."),
    }

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="cpp")
        clean_code = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), source_code, flags=re.DOTALL)
        lines = clean_code.splitlines()
        result.total_lines = len(source_code.splitlines())

        self._extract_cpp_structures(lines, result)
        self._check_unsafe_functions(lines, result)
        self._check_dangerous_patterns(lines, result)
        self._check_secrets(lines, result)

        result.findings = _postprocess_findings(result.findings, source_code.splitlines())
        return result


    def _extract_cpp_structures(self, lines: list, result: StaticAnalysisResult):
        for line in lines:
            inc_match = re.match(r'^\s*#include\s+[<"]([^>"]+)[>"]', line)
            if inc_match:
                result.imports.append(inc_match.group(1))

        for idx, line in enumerate(lines, start=1):
            cls_match = re.search(r'\b(class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if cls_match and not line.strip().startswith("//"):
                result.classes.append({"name": cls_match.group(2), "line": idx})

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
            if stripped.startswith("//") or _is_suppressed(line):
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
            if stripped.startswith("//") or _is_suppressed(line):
                continue

            if re.search(r'\bprintf\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)\s*;', stripped):
                result.findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=idx,
                    message="Format String Açığı: 'printf' doğrudan değişkene paslanmış.",
                    suggestion='Format belirteci kullanın: printf("%s", var);'
                ))

            if re.search(r'\b(malloc|calloc|realloc)\s*\(', stripped):
                result.findings.append(Finding(
                    severity="MEDIUM",
                    category="Memory Safety",
                    line=idx,
                    message="Dinamik bellek tahsisi: NULL kontrolü ve free() unutulmamalıdır.",
                    suggestion="C++ yazıyorsanız RAII ve std::unique_ptr / std::make_unique tercih edin."
                ))

            if re.search(r'\bnew\s+[a-zA-Z_][a-zA-Z0-9_]*\b', stripped) and "delete" not in stripped:
                result.findings.append(Finding(
                    severity="LOW",
                    category="Memory Safety",
                    line=idx,
                    message="Ham 'new' kullanımı bellek sızıntısına (memory leak) yol açabilir.",
                    suggestion="Smart pointer (std::make_unique / std::make_shared) kullanın."
                ))

    def _check_secrets(self, lines: list, result: StaticAnalysisResult):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or _is_suppressed(line):
                continue
            for kw in SECRET_KEYWORDS:
                pattern = re.compile(rf'{kw}\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
                match = pattern.search(stripped)
                if match:
                    value = match.group(1)
                    if SECRET_VALUE_PATTERN.match(value) and value.lower() not in PLACEHOLDER_VALUES:
                        result.findings.append(Finding(
                            severity="HIGH",
                            category="Security",
                            line=idx,
                            message=f"Hard-coded C/C++ '{kw}' değeri tespit edildi.",
                            suggestion="Hassas değerleri ortam değişkenlerinden veya güvenli bir yapılandırma dosyasından okuyun.",
                            confidence=0.8,
                        ))



class JavaAnalyzer:
    """Java için statik kod analizörü (Regex ve desen taraması)."""

    UNSAFE_CALLS = {
        "Runtime.exec":          ("HIGH",   "Kabuk Enjeksiyonu Riski: 'Runtime.exec()' harici komut çalıştırır.", "ProcessBuilder ile komut dizisini liste olarak geçirin."),
        "ProcessBuilder":        ("MEDIUM", "ProcessBuilder kullanımı: komut argümanlarının doğrulanması gerekir.", "Kullanıcı girdisini doğrudan komuta eklemeyin."),
        "ObjectInputStream":     ("HIGH",   "Güvensiz Deserialization: 'ObjectInputStream.readObject()' uzaktan kod yürütümüne neden olabilir.", "Güvenilmeyen kaynaklardan deserialization yapmaktan kaçının."),
        "printStackTrace":       ("LOW",    "'printStackTrace()' iç uygulama detaylarını açığa çıkarır.", "Yapılandırılmış bir logger (SLF4J/Log4j) kullanın."),
    }

    SECRET_KEYWORDS_JAVA = [
        "password", "passwd", "secret", "apikey", "api_key",
        "token", "auth_token", "private_key", "client_secret",
    ]

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="java")
        clean_code = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), source_code, flags=re.DOTALL)
        lines = clean_code.splitlines()
        result.total_lines = len(source_code.splitlines())

        self._extract_java_structures(lines, result)
        self._check_unsafe_calls(lines, result)
        self._check_sql_injection(lines, result)
        self._check_empty_catch(lines, result)
        self._check_string_equality(lines, result)
        self._check_secrets(lines, result)
        self._check_sensitive_logging(lines, result)

        result.findings = _postprocess_findings(result.findings, source_code.splitlines())
        return result

    def _extract_java_structures(self, lines: list, result: StaticAnalysisResult):
        import_re = re.compile(r'^\s*import\s+([\w.]+)\s*;')
        class_re  = re.compile(r'\b(class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)')
        func_re   = re.compile(
            r'(?:public|private|protected|static|final|synchronized|\s)+'
            r'[\w<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
        )

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue

            m = import_re.match(line)
            if m:
                result.imports.append(m.group(1))

            m = class_re.search(line)
            if m:
                result.classes.append({"name": m.group(2), "line": idx})

            m = func_re.search(line)
            if m:
                name = m.group(1)
                if name not in ("if", "while", "for", "switch", "catch", "try"):
                    result.functions.append({"name": name, "line": idx, "param_count": 0, "length": 0})

    def _check_unsafe_calls(self, lines: list, result: StaticAnalysisResult):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or _is_suppressed(line):
                continue
            for pattern, (sev, msg, sug) in self.UNSAFE_CALLS.items():
                if pattern in stripped:
                    result.findings.append(Finding(
                        severity=sev, category="Security", line=idx, message=msg, suggestion=sug
                    ))

    def _check_sql_injection(self, lines: list, result: StaticAnalysisResult):
        sql_keywords = re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b', re.IGNORECASE)
        concat_pattern = re.compile(r'["\']\s*\+\s*\w|\w\s*\+\s*["\']')
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or _is_suppressed(line):
                continue
            if sql_keywords.search(stripped) and concat_pattern.search(stripped):
                result.findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=idx,
                    message="SQL Injection riski: SQL sorgusu string birleştirme ile oluşturuluyor.",
                    suggestion="PreparedStatement veya JPA parametrik sorgu kullanın.",
                    confidence=0.85,
                ))

    def _check_empty_catch(self, lines: list, result: StaticAnalysisResult):
        in_catch = False
        catch_line = 0
        brace_depth = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or _is_suppressed(line):
                continue

            if re.search(r'\bcatch\s*\(', stripped):
                in_catch = True
                catch_line = idx
                brace_depth = 0

            if in_catch:
                brace_depth += stripped.count("{") - stripped.count("}")
                if brace_depth < 0 or (brace_depth == 0 and "{" in stripped and "}" in stripped):
                    body = stripped[stripped.find("{") + 1: stripped.rfind("}") if "}" in stripped else len(stripped)].strip()
                    if not body or body in ("//", ""):
                        result.findings.append(Finding(
                            severity="MEDIUM",
                            category="Code Quality",
                            line=catch_line,
                            message="Boş 'catch' bloğu: hata sessizce yutulur.",
                            suggestion="En azından loglama yapın: logger.error(e.getMessage(), e);",
                        ))
                    in_catch = False

    def _check_string_equality(self, lines: list, result: StaticAnalysisResult):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or _is_suppressed(line):
                continue
            if re.search(r'==\s*"[^"]*"', stripped) or re.search(r'"[^"]*"\s*==', stripped):
                result.findings.append(Finding(
                    severity="MEDIUM",
                    category="Potential Bugs",
                    line=idx,
                    message="String karşılaştırmasında '==' kullanımı referans karşılaştırması yapar.",
                    suggestion="String karşılaştırması için '.equals()' metodunu kullanın.",
                ))

    def _check_secrets(self, lines: list, result: StaticAnalysisResult):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or _is_suppressed(line):
                continue
            for kw in self.SECRET_KEYWORDS_JAVA:
                pattern = re.compile(rf'\b{kw}\b\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
                match = pattern.search(stripped)
                if match:
                    value = match.group(1)
                    if SECRET_VALUE_PATTERN.match(value) and value.lower() not in PLACEHOLDER_VALUES:
                        result.findings.append(Finding(
                            severity="HIGH",
                            category="Security",
                            line=idx,
                            message=f"Hard-coded '{kw}' değeri tespit edildi.",
                            suggestion="Hassas değerleri environment variable veya güvenli bir secret manager ile okuyun.",
                            confidence=0.8,
                        ))

    def _check_sensitive_logging(self, lines: list, result: StaticAnalysisResult):
        log_pattern    = re.compile(r'\b(System\.out\.print|println|logger\.(info|debug|warn|error))\b', re.IGNORECASE)
        secret_pattern = re.compile(r'\b(password|passwd|secret|token|apikey)\b', re.IGNORECASE)
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or _is_suppressed(line):
                continue
            if log_pattern.search(stripped) and secret_pattern.search(stripped):
                result.findings.append(Finding(
                    severity="MEDIUM",
                    category="Security",
                    line=idx,
                    message="Log satırında hassas veri (şifre/token) yazdırılıyor olabilir.",
                    suggestion="Hassas alanları loglara yazmaktan kaçının veya maskeleme uygulayın.",
                    confidence=0.75,
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
                        if val and SECRET_VALUE_PATTERN.match(val) and val.lower() not in PLACEHOLDER_VALUES:
                            self.findings.append(Finding(
                                severity="HIGH",
                                category="Security",
                                line=node.lineno,
                                message=f"Hard-coded '{keyword}' değeri tespit edildi: '{target.id}'.",
                                suggestion="Hassas değerleri .env dosyasına veya environment variable'a taşıyın.",
                                confidence=0.8,
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


class CSSAnalyzer:
    """CSS Statik Analizör sınıfı."""

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="css")
        lines = source_code.splitlines()
        result.total_lines = len(lines)
        findings = []

        open_braces = source_code.count("{")
        close_braces = source_code.count("}")
        if open_braces != close_braces:
            result.syntax_error = f"CSS süslü parantez dengesizliği: {open_braces} açılan '{{' vs {close_braces} kapanan '}}'."

        important_count = 0
        for i, line in enumerate(lines, 1):
            line_str = line.strip()

            if "!important" in line_str:
                important_count += 1
                if important_count > 3:
                    findings.append(Finding(
                        severity="MEDIUM",
                        category="Code Quality",
                        line=i,
                        message="Aşırı '!important' kullanımı tespit edildi.",
                        suggestion="CSS özgüllüğünü (specificity) artırmak için '!important' yerine daha spesifik seçiciler kullanın.",
                        confidence=0.9
                    ))

            if "http://" in line_str and not line_str.startswith("/*"):
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="Güvensiz HTTP kaynağı (font/image/asset) çağrılıyor.",
                    suggestion="Tarayıcının 'Mixed Content' engellemesini önlemek için HTTPS protokolü ('https://') kullanın.",
                    confidence=1.0
                ))

            if line_str.startswith("@import"):
                findings.append(Finding(
                    severity="MEDIUM",
                    category="Performance",
                    line=i,
                    message="@import kullanımı sayfa yüklenme performansını olumsuz etkiler.",
                    suggestion="CSS dosyalarını HTML içerisinde <link rel='stylesheet'> ile paralel yükleyin.",
                    confidence=0.85
                ))

            if "z-index" in line_str:
                match = re.search(r"z-index\s*:\s*(\d+)", line_str)
                if match and int(match.group(1)) >= 9999:
                    findings.append(Finding(
                        severity="LOW",
                        category="Maintainability",
                        line=i,
                        message=f"Aşırı yüksek z-index değeri: {match.group(1)}.",
                        suggestion="Düzenli bir katman (stacking context) mimarisi oluşturun ve z-index değerlerini makul seviyede tutun.",
                        confidence=0.9
                    ))

        result.findings = _postprocess_findings(findings, lines)
        return result


class HTMLAnalyzer:
    """HTML Statik Analizör sınıfı."""

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="html")
        lines = source_code.splitlines()
        result.total_lines = len(lines)
        findings = []

        for i, line in enumerate(lines, 1):
            line_str = line.strip()

            if re.search(r'on\w+\s*=\s*["\']', line_str, re.IGNORECASE):
                findings.append(Finding(
                    severity="MEDIUM",
                    category="Security",
                    line=i,
                    message="Satır içi (inline) JavaScript olay dinleyicisi (event handler) tespiti.",
                    suggestion="Güvenlik (CSP) ve sürdürülebilirlik için olay dinleyicilerini ayrı JS dosyalarında addEventListener ile ekleyin.",
                    confidence=0.9
                ))

            if 'target="_blank"' in line_str or "target='_blank'" in line_str:
                if 'rel="noopener' not in line_str and "rel='noopener" not in line_str:
                    findings.append(Finding(
                        severity="MEDIUM",
                        category="Security",
                        line=i,
                        message="'target=\"_blank\"' kullanımında 'rel=\"noopener noreferrer\"' eksik.",
                        suggestion="Tabnabbing ve performans açıklarını önlemek için rel=\"noopener noreferrer\" ekleyin.",
                        confidence=1.0
                    ))

            if re.search(r'<(script|link)\s+[^>]*src=["\']http://', line_str, re.IGNORECASE):
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="Güvensiz HTTP script/style kaynağı dahil ediliyor.",
                    suggestion="Ortadaki adam (MitM) saldırılarını önlemek için yalnızca HTTPS protokolünü kullanın.",
                    confidence=1.0
                ))

            if "<img" in line_str and "alt=" not in line_str:
                findings.append(Finding(
                    severity="LOW",
                    category="Accessibility",
                    line=i,
                    message="<img> etiketinde 'alt' özniteliği eksik.",
                    suggestion="Erişilebilirlik ve SEO için resimlere açıklayıcı 'alt' metni ekleyin.",
                    confidence=0.85
                ))

        result.findings = _postprocess_findings(findings, lines)
        return result


class JSAnalyzer:
    """JavaScript / TypeScript Statik Analizör sınıfı."""

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="javascript")
        lines = source_code.splitlines()
        result.total_lines = len(lines)
        findings = []

        for i, line in enumerate(lines, 1):
            line_str = line.strip()

            if "innerHTML" in line_str:
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="'innerHTML' kullanımı XSS (Cross-Site Scripting) zafiyeti riski taşır.",
                    suggestion="'textContent', 'innerText' veya güvenli DOM oluşturma metotlarını (createElement) tercih edin.",
                    confidence=0.95
                ))

            if "document.write(" in line_str:
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="'document.write()' kullanımı güvensizdir ve sayfa performansını bozar.",
                    suggestion="DOM manipülasyonları için modern W3C DOM API'lerini kullanın.",
                    confidence=1.0
                ))

            if "eval(" in line_str:
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="Tehlikeli 'eval()' fonksiyonu kullanımı.",
                    suggestion="Dinamik kod çalıştırmaktan kaçının; güvenlik ve optimizasyon sorunlarına yol açar.",
                    confidence=1.0
                ))

            if re.search(r"localStorage\.(setItem|getItem)\s*\(\s*['\"](token|auth|password|secret)", line_str, re.IGNORECASE):
                findings.append(Finding(
                    severity="MEDIUM",
                    category="Security",
                    line=i,
                    message="Hassas veriler (token/şifre) localStorage üzerinde saklanıyor.",
                    suggestion="XSS saldırılarında çalınmaması için oturum jetonlarını HttpOnly Cookie içinde saklayın.",
                    confidence=0.9
                ))

            for keyword in SECRET_KEYWORDS:
                if f"{keyword}" in line_str.lower() and "=" in line_str:
                    match = re.search(r'["\']([A-Za-z0-9+/=_\-]{12,})["\']', line_str)
                    if match:
                        val = match.group(1)
                        if val.lower() not in PLACEHOLDER_VALUES and SECRET_VALUE_PATTERN.match(val):
                            findings.append(Finding(
                                severity="HIGH",
                                category="Security",
                                line=i,
                                message=f"Hard-coded JS '{keyword}' değeri tespit edildi.",
                                suggestion="Hassas anahtarları frontend kodunda tutmayın; ortam değişkenleri veya backend API üzerinden kullanın.",
                                confidence=0.85
                            ))

            if "console.log(" in line_str:
                if any(k in line_str.lower() for k in ["pass", "token", "user", "data", "key"]):
                    findings.append(Finding(
                        severity="LOW",
                        category="Code Quality",
                        line=i,
                        message="Hassas olabilecek veri 'console.log' ile tarayıcı konsoluna yazdırılıyor.",
                        suggestion="Üretim ortamına çıkmadan önce konsol loglarını kaldırın veya log seviyelerini düzenleyin.",
                        confidence=0.75
                    ))

        result.findings = _postprocess_findings(findings, lines)
        return result


class CSharpAnalyzer:
    """C# (.cs) Statik Analizör sınıfı."""

    def analyze(self, filepath: str, source_code: str) -> StaticAnalysisResult:
        result = StaticAnalysisResult(filepath=filepath, source_code=source_code, language="csharp")
        lines = source_code.splitlines()
        result.total_lines = len(lines)
        findings = []

        open_braces = source_code.count("{")
        close_braces = source_code.count("}")
        if open_braces != close_braces:
            result.syntax_error = f"C# süslü parantez dengesizliği: {open_braces} açılan '{{' vs {close_braces} kapanan '}}'."

        for i, line in enumerate(lines, 1):
            line_str = line.strip()

            # 1. SQL Injection
            if re.search(r'new\s+SqlCommand\s*\(\s*["\'].*?\+\s*\w+|SELECT\s+.*?\+\s*\w+', line_str, re.IGNORECASE):
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="SQL Injection riski: SQL sorgusu string birleştirme ile oluşturuluyor.",
                    suggestion="Parametreli sorgu kullanın: cmd.Parameters.AddWithValue(\"@param\", value);",
                    confidence=0.95
                ))

            # 2. BinaryFormatter Deserialization
            if "BinaryFormatter" in line_str and "Deserialize(" in line_str:
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="Güvensiz Deserialization: 'BinaryFormatter' uzaktan kod yürütümüne (RCE) yol açabilir.",
                    suggestion="'BinaryFormatter' yerine System.Text.Json veya Newtonsoft.Json kullanın.",
                    confidence=1.0
                ))

            # 3. Process.Start Command Injection
            if "Process.Start(" in line_str and "+" in line_str:
                findings.append(Finding(
                    severity="HIGH",
                    category="Security",
                    line=i,
                    message="Process.Start kullanımı: Kullanıcı girdisiyle komut birleştirme kabuk enjeksiyonuna yol açabilir.",
                    suggestion="ProcessStartInfo.ArgumentList kullanarak argümanları güvenli şekilde geçirin.",
                    confidence=0.9
                ))

            # 4. Hard-coded Connection String / Secrets
            for keyword in SECRET_KEYWORDS:
                if keyword in line_str.lower() and ("=" in line_str or "ConnectionString" in line_str):
                    match = re.search(r'["\']([A-Za-z0-9+/=_\-]{12,})["\']', line_str)
                    if match:
                        val = match.group(1)
                        if val.lower() not in PLACEHOLDER_VALUES and SECRET_VALUE_PATTERN.match(val):
                            findings.append(Finding(
                                severity="HIGH",
                                category="Security",
                                line=i,
                                message=f"Hard-coded C# '{keyword}' veya bağlantı dizesi tespit edildi.",
                                suggestion="Hassas anahtarları ve Connection String'leri appsettings.json veya Environment Variable üzerinden okuyun.",
                                confidence=0.85
                            ))

            # 5. Empty Catch
            if line_str.startswith("catch") and ("{ }" in line_str or "{}" in line_str):
                findings.append(Finding(
                    severity="MEDIUM",
                    category="Code Quality",
                    line=i,
                    message="Boş 'catch' bloğu: Hata sessizce yutuluyor.",
                    suggestion="Hataları loglayın: _logger.LogError(ex, \"Hata oluştu\");",
                    confidence=0.95
                ))

            # 6. Missing Using Statement / IDisposable
            if re.search(r'new\s+(StreamReader|FileStream|SqlConnection|HttpClient)\s*\(', line_str) and not line_str.startswith("using"):
                findings.append(Finding(
                    severity="MEDIUM",
                    category="Performance",
                    line=i,
                    message="IDisposable nesnesi 'using' bloğu olmadan oluşturuluyor (Resource Leak riski).",
                    suggestion="Bellek sızıntısını önlemek için 'using var resource = new ...' desenini kullanın.",
                    confidence=0.85
                ))

        result.findings = _postprocess_findings(findings, lines)
        return result
