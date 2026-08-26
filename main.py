import sys
import os
import argparse

try:
    # pyrefly: ignore [missing-import]
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from analyzer import StaticAnalyzer
from llm_reviewer import LLMReviewer, AIReviewResult
from reporter import Reporter, ProjectReporter

SUPPORTED_EXTENSIONS = (".py", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".java")

RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Code Review Assistant — Tek dosya veya tüm proje klasörünü analiz eder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py examples/hatali_kod.py
  python main.py examples/hatali_kod.cpp --no-ai
  python main.py --dir myproject/
  python main.py --dir myproject/ --no-ai
        """,
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        default=None,
        help="Analiz edilecek kaynak dosya yolu (.py, .c, .cpp, .java, ...)",
    )
    parser.add_argument(
        "--dir", "-d",
        dest="directory",
        default=None,
        help="Tüm projeyi tara: klasör yolunu girin (özyinelemeli)",
    )
    parser.add_argument(
        "--no-ai", "--static-only",
        dest="no_ai",
        action="store_true",
        default=False,
        help="AI incelemesini atla, yalnızca statik analiz çalıştır",
    )
    return parser.parse_args()


def validate_file(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        print(f"\n[!] Hata: Dosya bulunamadi: '{filepath}'")
        return False
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"\n[~] Uyari: '{filepath}' desteklenen bir uzantiya sahip degil ({', '.join(SUPPORTED_EXTENSIONS)}).")
        print("   Devam etmek icin Enter'a basin veya Ctrl+C ile cikin...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCikiliyor.")
            return False
    return True


def run_single(filepath: str, no_ai: bool):
    if not validate_file(filepath):
        sys.exit(1)

    print(f"\nStatik analiz calistirilıyor: {filepath} ...")
    static_result = StaticAnalyzer().analyze(filepath)

    if no_ai:
        ai_result = AIReviewResult(
            skipped=True,
            error="--no-ai bayragi ile AI incelemesi atlandi.",
        )
    else:
        print("AI incelemesi calistiriliyor ...")
        ai_result = LLMReviewer().review(
            source_code=static_result.source_code,
            filepath=filepath,
        )

    reporter = Reporter(static_result=static_result, ai_result=ai_result)
    reporter.print_report()
    reporter.save_report()


def run_directory(directory: str, no_ai: bool):
    if not os.path.isdir(directory):
        print(f"\n[!] Hata: Klasor bulunamadi: '{directory}'")
        sys.exit(1)

    from scanner import ProjectScanner

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}{'PROJE TARAMASI':^72}{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print(f"  Klasor  : {os.path.abspath(directory)}")
    print(f"  AI Modu : {'Kapali' if no_ai else 'Acik'}")
    print(f"{BOLD}{'-' * 72}{RESET}")

    scanner = ProjectScanner(no_ai=no_ai)
    files = scanner.collect_files(directory)

    if not files:
        print(f"\n[~] Desteklenen uzantili dosya bulunamadi.")
        sys.exit(0)

    print(f"\n  Bulunan dosya sayisi: {len(files)}")
    for f in files:
        print(f"    - {os.path.relpath(f, directory)}")
    print()

    def progress(i, total, filepath):
        rel = os.path.relpath(filepath, directory)
        print(f"  [{i+1}/{total}] Taranıyor: {rel} ...")

    project_result = scanner.scan(directory, progress_callback=progress)

    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"{BOLD}{'PROJE OZETI':^72}{RESET}")
    print(f"{BOLD}{'=' * 72}{RESET}")
    print(f"  Toplam dosya      : {project_result.total_files}")
    print(f"  Toplam satir      : {project_result.total_lines}")
    print(f"  {RED}[!] HIGH bulgular : {project_result.total_high}{RESET}")
    print(f"  {YELLOW}[~] MEDIUM bulgu  : {project_result.total_medium}{RESET}")
    print(f"  {GREEN}[-] LOW bulgular  : {project_result.total_low}{RESET}")
    print(f"      TOPLAM bulgu  : {project_result.total_findings}")
    print(f"{BOLD}{'-' * 72}{RESET}")

    print(f"\n{BOLD}  EN COK SORUNLU DOSYALAR:{RESET}")
    for fr in project_result.sorted_by_risk()[:10]:
        rel = os.path.relpath(fr.filepath, directory)
        lang = fr.static.language.upper()
        h, m, l = fr.high_count, fr.medium_count, fr.low_count
        bar = f"{RED}H:{h}{RESET} {YELLOW}M:{m}{RESET} {GREEN}L:{l}{RESET}"
        print(f"    {bar}  [{lang}] {rel}")

    report_path = ProjectReporter(project_result).save_report()
    print(f"\n{BOLD}{'=' * 72}{RESET}")
    print(f"  [+] Proje raporu kaydedildi: {report_path}")
    print(f"{BOLD}{'=' * 72}{RESET}\n")


def main():
    args = parse_args()

    if args.directory:
        run_directory(args.directory, args.no_ai)
    elif args.filepath:
        run_single(args.filepath, args.no_ai)
    else:
        print("[!] Hata: Bir dosya yolu veya --dir ile klasor yolu belirtmelisiniz.")
        print("    Ornek: python main.py dosya.py")
        print("    Ornek: python main.py --dir proje_klasoru/")
        sys.exit(1)


if __name__ == "__main__":
    main()
