import os
from datetime import datetime
from typing import Optional, List

from analyzer import StaticAnalysisResult, Finding
from llm_reviewer import AIReviewResult, AIFinding

RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

REPORTS_DIR = "reports"
WIDTH       = 72


def _severity_color(severity: str) -> str:
    return {"HIGH": RED, "MEDIUM": YELLOW, "LOW": GREEN}.get(severity.upper(), "")


def _severity_badge(severity: str) -> str:
    return {"HIGH": "[!]", "MEDIUM": "[~]", "LOW": "[-]"}.get(severity.upper(), "[ ]")


class Reporter:
    def __init__(self, static_result: StaticAnalysisResult, ai_result: AIReviewResult):
        self.static    = static_result
        self.ai        = ai_result
        self.timestamp = datetime.now()

    def print_report(self):
        self._print_header()
        self._print_summary()
        self._print_static_findings()
        self._print_ai_findings()
        self._print_severity_counts()
        self._print_footer()

    def _print_header(self):
        print()
        print(f"{BOLD}{'=' * WIDTH}{RESET}")
        print(f"{BOLD}{'AI CODE REVIEW ASSISTANT':^{WIDTH}}{RESET}")
        print(f"{BOLD}{'=' * WIDTH}{RESET}")
        print(f"  Dosya : {self.static.filepath}")
        print(f"  Tarih : {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.ai.model_used:
            print(f"  Model : {self.ai.model_used}")
        print(f"{BOLD}{'-' * WIDTH}{RESET}")

    def _print_summary(self):
        print(f"\n{BOLD}OZET{RESET}")
        print(f"  Toplam satir    : {self.static.total_lines}")
        print(f"  Fonksiyon sayisi: {self.static.function_count}")
        print(f"  Sinif sayisi    : {self.static.class_count}")
        if self.static.imports:
            print(f"  Import sayisi   : {len(self.static.imports)}")
        if self.static.syntax_error:
            print(f"\n  {RED}{BOLD}[!] SYNTAX HATASI: {self.static.syntax_error}{RESET}")

    def _print_static_findings(self):
        print(f"\n{BOLD}{'─' * WIDTH}{RESET}")
        print(f"{BOLD}STATIC ANALYSIS{RESET}")
        print(f"{DIM}Python AST ile tespit edilen gercek bulgular{RESET}")
        print(f"{BOLD}{'─' * WIDTH}{RESET}")

        if not self.static.findings:
            print(f"  {GREEN}[+] Statik analiz bulgusu yok.{RESET}")
        else:
            for f in self.static.findings:
                self._print_finding(
                    severity=f.severity,
                    category=f.category,
                    line=str(f.line) if f.line else None,
                    function_name=None,
                    message=f.message,
                    suggestion=f.suggestion,
                )

    def _print_ai_findings(self):
        print(f"\n{BOLD}{'─' * WIDTH}{RESET}")
        print(f"{BOLD}AI REVIEW{RESET}")

        if self.ai.skipped:
            print(f"  {YELLOW}[~] AI incelemesi atlandi: {self.ai.error}{RESET}")
            return

        if self.ai.error:
            print(f"  {RED}[!] AI hatasi: {self.ai.error}{RESET}")
            return

        print(f"{DIM}LLM tabanli analiz — dogrulanamayan konular kapsam disidir{RESET}")
        print(f"{BOLD}{'─' * WIDTH}{RESET}")

        if not self.ai.findings:
            if self.ai.parse_failed:
                preview = self.ai.raw_response[:300].replace("\n", " ")
                print(f"  {YELLOW}[~] Model cevap verdi ama JSON parse edilemedi.{RESET}")
                print(f"  {DIM}    Ham yanit onizleme: {preview}...{RESET}")
            else:
                print(f"  {GREEN}[+] AI inceleme bulgusu yok.{RESET}")
        else:
            for f in self.ai.findings:
                self._print_finding(
                    severity=f.severity,
                    category=f.category,
                    line=f.line_range,
                    function_name=f.function_name,
                    message=f.message,
                    suggestion=f.suggestion,
                )

    def _print_finding(
        self,
        severity: str,
        category: str,
        line: Optional[str],
        function_name: Optional[str],
        message: str,
        suggestion: Optional[str],
    ):
        color  = _severity_color(severity)
        badge  = _severity_badge(severity)
        meta   = ""
        if line:
            meta += f"  line {line}"
        if function_name:
            meta += f"  fn:{function_name}"

        print()
        print(f"  {color}{BOLD}{badge} [{severity}] {category}{RESET}{DIM}{meta}{RESET}")
        print(f"      {message}")
        if suggestion:
            print(f"      {DIM}>> {suggestion}{RESET}")

    def _print_severity_counts(self):
        all_findings = list(self.static.findings)
        if not self.ai.skipped and not self.ai.error:
            all_findings += self.ai.findings

        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in all_findings:
            sev = getattr(f, "severity", "LOW").upper()
            counts[sev] = counts.get(sev, 0) + 1

        print(f"\n{BOLD}{'─' * WIDTH}{RESET}")
        print(f"{BOLD}BULGULAR{RESET}")
        print(f"  {RED}[!] HIGH  : {counts['HIGH']}{RESET}")
        print(f"  {YELLOW}[~] MEDIUM: {counts['MEDIUM']}{RESET}")
        print(f"  {GREEN}[-] LOW   : {counts['LOW']}{RESET}")
        print(f"      TOPLAM: {sum(counts.values())}")

    def _print_footer(self):
        print(f"\n{BOLD}{'=' * WIDTH}{RESET}")
        print(f"  [+] Rapor kaydedildi: {self._get_report_path()}")
        print(f"{BOLD}{'=' * WIDTH}{RESET}\n")

    def save_report(self) -> str:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = self._get_report_path()
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self._build_report_lines()))
        return report_path

    def _get_report_path(self) -> str:
        return os.path.join(REPORTS_DIR, f"code_review_{self.timestamp.strftime('%Y_%m_%d_%H%M')}.txt")

    def _build_report_lines(self) -> list:
        w, hr, thin = 72, "=" * 72, "-" * 72

        lines = [
            hr,
            "AI CODE REVIEW REPORT".center(w),
            hr,
            f"Dosya          : {self.static.filepath}",
            f"Analiz tarihi  : {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if self.ai.model_used:
            lines.append(f"AI Model       : {self.ai.model_used}")

        lines += [hr, "", "OZET", thin,
            f"Toplam satir    : {self.static.total_lines}",
            f"Fonksiyon sayisi: {self.static.function_count}",
            f"Sinif sayisi    : {self.static.class_count}",
            f"Import sayisi   : {len(self.static.imports)}",
        ]

        if self.static.syntax_error:
            lines += ["", f"[!] SYNTAX HATASI: {self.static.syntax_error}"]

        if self.static.functions:
            lines += ["", "Fonksiyonlar:"]
            for fn in self.static.functions:
                lines.append(f"  - {fn['name']} (line {fn['line']}, {fn['param_count']} parametre, {fn['length']} satir)")

        if self.static.classes:
            lines += ["", "Siniflar:"]
            for cls in self.static.classes:
                lines.append(f"  - {cls['name']} (line {cls['line']})")

        if self.static.imports:
            lines += ["", "Importlar:"]
            for imp in self.static.imports:
                lines.append(f"  - {imp}")

        lines += ["", hr, "STATIC ANALYSIS", thin]
        if not self.static.findings:
            lines.append("[+] Statik analiz bulgusu yok.")
        else:
            for f in self.static.findings:
                lines += self._format_finding_txt(f.severity, f.category, str(f.line) if f.line else None, None, f.message, f.suggestion)

        lines += ["", hr, "AI REVIEW", thin]
        if self.ai.skipped:
            lines.append(f"[~] AI incelemesi atlandi: {self.ai.error}")
        elif self.ai.error:
            lines.append(f"[!] AI hatasi: {self.ai.error}")
        elif not self.ai.findings:
            lines.append("[+] AI inceleme bulgusu yok.")
        else:
            for f in self.ai.findings:
                lines += self._format_finding_txt(f.severity, f.category, f.line_range, f.function_name, f.message, f.suggestion)

        all_findings = list(self.static.findings)
        if not self.ai.skipped and not self.ai.error:
            all_findings += self.ai.findings
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in all_findings:
            sev = getattr(f, "severity", "LOW").upper()
            counts[sev] = counts.get(sev, 0) + 1

        lines += ["", hr, "BULGU OZETI", thin,
            f"[!] HIGH  : {counts['HIGH']}",
            f"[~] MEDIUM: {counts['MEDIUM']}",
            f"[-] LOW   : {counts['LOW']}",
            f"    TOPLAM: {sum(counts.values())}",
            "", hr,
        ]
        return lines

    def _format_finding_txt(
        self,
        severity: str,
        category: str,
        line: Optional[str],
        function_name: Optional[str],
        message: str,
        suggestion: Optional[str],
    ) -> list:
        badge  = _severity_badge(severity)
        header = f"{badge} [{severity}] {category}"
        if line:
            header += f"  |  line {line}"
        if function_name:
            header += f"  |  fn:{function_name}"
        result = ["", header, f"    {message}"]
        if suggestion:
            result.append(f"    >> {suggestion}")
        return result


class ProjectReporter:
    def __init__(self, project_result):
        self.project = project_result
        self.timestamp = datetime.now()

    def save_report(self) -> str:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(
            REPORTS_DIR,
            f"project_review_{self.timestamp.strftime('%Y_%m_%d_%H%M')}.txt"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self._build_lines()))
        return report_path

    def _build_lines(self) -> list:
        w   = 72
        hr  = "=" * w
        thin = "-" * w
        lines = [
            hr,
            "AI CODE REVIEW — PROJE RAPORU".center(w),
            hr,
            f"Klasor         : {self.project.directory}",
            f"Analiz tarihi  : {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Toplam dosya   : {self.project.total_files}",
            f"Toplam satir   : {self.project.total_lines}",
            "",
            "PROJE BULGU OZETI",
            thin,
            f"[!] HIGH  : {self.project.total_high}",
            f"[~] MEDIUM: {self.project.total_medium}",
            f"[-] LOW   : {self.project.total_low}",
            f"    TOPLAM: {self.project.total_findings}",
            "",
            hr,
            "DOSYA BAZLI DETAYLAR",
            hr,
        ]

        for fr in self.project.sorted_by_risk():
            rel  = os.path.relpath(fr.filepath, self.project.directory)
            lang = fr.static.language.upper()
            lines += [
                "",
                thin,
                f"DOSYA: {rel}  [{lang}]",
                f"  Satir: {fr.static.total_lines} | "
                f"H:{fr.high_count} M:{fr.medium_count} L:{fr.low_count}",
                thin,
            ]

            if fr.static.syntax_error:
                lines.append(f"  [!] SYNTAX HATASI: {fr.static.syntax_error}")

            if fr.static.findings:
                lines.append("  Statik Analiz Bulgulari:")
                for f in fr.static.findings:
                    badge = _severity_badge(f.severity)
                    line_info = f"line {f.line}" if f.line else "genel"
                    lines.append(f"    {badge} [{f.severity}] {f.category} | {line_info}")
                    lines.append(f"        {f.message}")
                    if f.suggestion:
                        lines.append(f"        >> {f.suggestion}")

            if not fr.ai.skipped and not fr.ai.error:
                if fr.ai.findings:
                    lines.append("  AI Review Bulgulari:")
                    for f in fr.ai.findings:
                        badge = _severity_badge(f.severity)
                        line_info = f"line {f.line_range}" if f.line_range else "genel"
                        lines.append(f"    {badge} [{f.severity}] {f.category} | {line_info}")
                        lines.append(f"        {f.message}")
                        if f.suggestion:
                            lines.append(f"        >> {f.suggestion}")
                else:
                    lines.append("  [+] AI inceleme bulgusu yok.")
            elif fr.ai.skipped:
                lines.append(f"  [~] AI atlandi: {fr.ai.error}")
            elif fr.ai.error:
                lines.append(f"  [!] AI hatasi: {fr.ai.error}")


        lines += ["", hr]
        return lines

