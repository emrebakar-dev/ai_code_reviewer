import sys
import os
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from analyzer import StaticAnalyzer
from llm_reviewer import LLMReviewer, AIReviewResult
from reporter import Reporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Code Review Assistant — Python dosyalarını statik + AI ile analiz eder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py examples/hatali_kod.py
  python main.py dosya.py --no-ai
        """,
    )
    parser.add_argument("filepath", help="Analiz edilecek Python dosyasının yolu")
    parser.add_argument(
        "--no-ai", "--static-only",
        dest="no_ai",
        action="store_true",
        default=False,
        help="AI incelemesini atla, yalnızca statik analiz çalıştır",
    )
    return parser.parse_args()


SUPPORTED_EXTENSIONS = (".py", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".java")


def validate_file(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        print(f"\n❌ Hata: Dosya bulunamadı: '{filepath}'")
        return False
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"\n⚠️  Uyarı: '{filepath}' desteklenen bir dosya uzantısına sahip değil ({', '.join(SUPPORTED_EXTENSIONS)}).")
        print("   Devam etmek için Enter'a basın veya Ctrl+C ile çıkın...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nÇıkılıyor.")
            return False
    return True


def main():
    args = parse_args()

    if not validate_file(args.filepath):
        sys.exit(1)

    print(f"\nStatik analiz çalışıyor: {args.filepath} ...")
    static_result = StaticAnalyzer().analyze(args.filepath)

    if args.no_ai:
        ai_result = AIReviewResult(
            skipped=True,
            error="--no-ai bayrağı ile AI incelemesi atlandı.",
        )
    else:
        print("AI incelemesi çalışıyor ...")
        ai_result = LLMReviewer().review(
            source_code=static_result.source_code,
            filepath=args.filepath,
        )

    reporter = Reporter(static_result=static_result, ai_result=ai_result)
    reporter.print_report()
    reporter.save_report()


if __name__ == "__main__":
    main()
