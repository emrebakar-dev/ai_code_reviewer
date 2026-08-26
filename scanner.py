import os
import time
from dataclasses import dataclass, field
from typing import List, Tuple


from analyzer import StaticAnalyzer, StaticAnalysisResult
from llm_reviewer import LLMReviewer, AIReviewResult

SUPPORTED_EXTENSIONS = (".py", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".java")

SKIP_DIRS = {
    "__pycache__", ".git", ".hg", ".svn",
    "node_modules", "venv", ".venv", "env",
    "build", "dist", "target", "out",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    "migrations", "static", "media",
}


@dataclass
class FileResult:
    filepath: str
    static: StaticAnalysisResult
    ai: AIReviewResult

    @property
    def total_findings(self) -> int:
        ai_count = len(self.ai.findings) if not self.ai.skipped and not self.ai.error else 0
        return len(self.static.findings) + ai_count

    @property
    def high_count(self) -> int:
        return self._count("HIGH")

    @property
    def medium_count(self) -> int:
        return self._count("MEDIUM")

    @property
    def low_count(self) -> int:
        return self._count("LOW")

    def _count(self, sev: str) -> int:
        all_f = list(self.static.findings)
        if not self.ai.skipped and not self.ai.error:
            all_f += self.ai.findings
        return sum(1 for f in all_f if getattr(f, "severity", "").upper() == sev)


@dataclass
class ProjectScanResult:
    directory: str
    results: List[FileResult] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.results)

    @property
    def total_lines(self) -> int:
        return sum(r.static.total_lines for r in self.results)

    @property
    def total_high(self) -> int:
        return sum(r.high_count for r in self.results)

    @property
    def total_medium(self) -> int:
        return sum(r.medium_count for r in self.results)

    @property
    def total_low(self) -> int:
        return sum(r.low_count for r in self.results)

    @property
    def total_findings(self) -> int:
        return self.total_high + self.total_medium + self.total_low

    def sorted_by_risk(self) -> List[FileResult]:
        return sorted(self.results, key=lambda r: (r.high_count, r.medium_count, r.low_count), reverse=True)


class ProjectScanner:
    def __init__(self, no_ai: bool = False, model: str = None):
        self.no_ai = no_ai
        self.model = model

    def collect_files(self, directory: str) -> List[str]:
        collected = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for fname in sorted(files):
                _, ext = os.path.splitext(fname)
                if ext.lower() in SUPPORTED_EXTENSIONS:
                    collected.append(os.path.join(root, fname))
        return collected

    def scan(self, directory: str, progress_callback=None) -> ProjectScanResult:
        project_result = ProjectScanResult(directory=directory)
        files = self.collect_files(directory)

        analyzer = StaticAnalyzer()
        reviewer = LLMReviewer()
        if self.model:
            reviewer.model = self.model

        for i, filepath in enumerate(files):
            if progress_callback:
                progress_callback(i, len(files), filepath)

            try:
                static_result = analyzer.analyze(filepath)
            except Exception as exc:
                static_result = StaticAnalysisResult(
                    filepath=filepath,
                    source_code="",
                    syntax_error=str(exc),
                )

            if self.no_ai:
                ai_result = AIReviewResult(
                    skipped=True,
                    error="--no-ai bayragi ile AI incelemesi atlandi.",
                )
            else:
                # Boş dosyaları AI'ya gönderme
                if not static_result.source_code.strip():
                    ai_result = AIReviewResult(
                        skipped=True,
                        error="Kaynak kod boş — AI incelemesi atlandı.",
                    )
                else:
                    # Groq rate limit aşımını önlemek için dosyalar arası bekleme
                    if i > 0:
                        time.sleep(12)
                    try:
                        ai_result = reviewer.review(
                            source_code=static_result.source_code,
                            filepath=filepath,
                        )
                    except Exception as exc:
                        ai_result = AIReviewResult(error=str(exc))


            project_result.results.append(FileResult(
                filepath=filepath,
                static=static_result,
                ai=ai_result,
            ))

        return project_result
