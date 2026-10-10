"""Integration test script for testing Gemma vision translation and formatting."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

# Implementation note: see the surrounding code for the behavior described here.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lektor.adapters.ocr.vision_adapter import UniversalVisionTranslatorAdapter
from lektor.domain.conversion_models import DocumentScan, PageNumber


def ensure_server_running() -> None:
    """Ensures local LM Studio server is running."""
    for url in ["http://localhost:1234/v1/models", "http://127.0.0.1:1234/v1/models"]:
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(url)
                if resp.status_code in (200, 404):
                    return
        except Exception:
            pass

    print("[INFO] Budzenie lokalnego serwera LM Studio (lms server start)...")
    try:
        subprocess.run(["lms", "server", "start", "--cors"], capture_output=True, text=True, timeout=15)
        time.sleep(2.0)
    except Exception as exc:
        print(f"[WARN] Nie udaĹ‚o siÄ™ automatycznie uruchomiÄ‡ serwera lms: {exc}")


def run_translation_test(
    scan_file: Path,
    page_num: int,
    model_name: str = "gemma-4-12b",
    output_dir: Path | None = None,
) -> None:
    if not scan_file.exists():
        print(f"BĹÄ„D: Plik skanu nie istnieje: {scan_file}", file=sys.stderr)
        sys.exit(1)

    ensure_server_running()

    adapter = UniversalVisionTranslatorAdapter(
        model_name=model_name,
        timeout_sec=300.0,
    )
    scan = DocumentScan(
        page_number=PageNumber(page_num),
        scan_path=scan_file,
        dpi=300,
    )

    print("=" * 70)
    print("Rozpoczynanie testu translacji:")
    print(f"  Plik skanu : {scan_file}")
    print(f"  Numer str. : {page_num}")
    print(f"  Model      : {model_name}")
    print("=" * 70)

    t0 = time.perf_counter()
    result = adapter.translate_scan(scan)
    elapsed = time.perf_counter() - t0

    content = result.markdown_content
    chars_count = len(content)
    words_count = len(content.split())
    approx_tokens = int(chars_count / 3.5)
    speed = approx_tokens / elapsed if elapsed > 0 else 0.0

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"page_{page_num:03d}_{model_name.replace(':', '_').replace('/', '_')}.md"
        out_file.write_text(content, encoding="utf-8")
        print(f"Zapisano przetĹ‚umaczony plik: {out_file}")

    print("\n--- WYNIK TRANSLACJI MARKDOWN ---")
    print(content)
    print("-" * 70)
    print(f"Czas generowania : {elapsed:.2f} s")
    print(f"Znaki / SĹ‚owa    : {chars_count} znakĂłw / {words_count} sĹ‚Ăłw")
    print(f"Szacowana prÄ™dk. : ~{speed:.1f} tok/s")
    print(f"Wykryte diagramy : {len(result.diagrams)}")
    print(f"Bloki kodu       : {result.code_blocks_count}")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test translacji skanu z modelem Vision")
    parser.add_argument("--scan", type=str, required=True, help="ĹšcieĹĽka do pliku JPG")
    parser.add_argument("--page", type=int, required=True, help="Numer strony")
    parser.add_argument("--model", type=str, default="gemma-4-12b", help="Identyfikator modelu")
    parser.add_argument("--out", type=str, default="data/books/100_go_mistakes/pages", help="Katalog wyjĹ›ciowy")
    args = parser.parse_args()

    run_translation_test(
        scan_file=Path(args.scan),
        page_num=args.page,
        model_name=args.model,
        output_dir=Path(args.out),
    )


if __name__ == "__main__":
    main()
