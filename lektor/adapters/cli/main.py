"""CLI adapter and command-line entry point for Lektor."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from ...application.dtos import (
    BatchSynthesisCommand,
    ConvertBookCommand,
    PreviewPageQuery,
    SynthesizePageCommand,
)
from ...application.ports.container_ports import ApplicationContainerProtocol
from ...application.ports.storage_ports import BookRepositoryProtocol
from ...application.ports.telemetry_ports import ProgressReporterProtocol
from ...domain.audio_models import SynthesisConfig, SynthesisResult
from ..tts.factory import TTSEngineFactory


class ConsoleProgressReporter(ProgressReporterProtocol):
    """Console progress reporter for batch operations."""

    def on_page_start(self, page_path: Path, current_idx: int, total_pages: int) -> None:
        print(f"\n[{current_idx}/{total_pages}] 📖 Rozpoczynam syntezę: {page_path.name}...")

    def on_page_complete(self, result: SynthesisResult) -> None:
        stats = result.stats
        rtf_str = f"{stats.rtf:.2f}" if stats.rtf > 0 else "0.00"
        print(
            f"  ✅ Zapisano: {result.audio_path.name} "
            f"({stats.audio_duration_sec:.1f}s audio w {stats.duration_sec:.1f}s | RTF: {rtf_str} | {stats.speed_factor:.1f}x speed)"
        )

    def on_skipped(self, page_path: Path, reason: str) -> None:
        print(f"  ⏩ Pominięto {page_path.name}: {reason}")

    def on_error(self, page_path: Path, error: Exception) -> None:
        print(f"  ❌ Błąd przetwarzania {page_path.name}: {error}")

    def check_cancellation(self) -> bool:
        return False


def _configure_windows_encoding() -> None:
    if sys.platform == "win32":
        try:
            reconfig = getattr(sys.stdout, "reconfigure", None)
            if callable(reconfig):
                reconfig(encoding="utf-8", errors="replace")
            reconfig_err = getattr(sys.stderr, "reconfigure", None)
            if callable(reconfig_err):
                reconfig_err(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _build_parser(default_audio_dir: str = "data/audio") -> argparse.ArgumentParser:
    """Builds command-line argument parser with configurable options."""
    parser = argparse.ArgumentParser(
        description="Lektor — Synteza mowy dla książki technicznej (Czysta Architektura)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Dostępne polecenia")

    # 1. preview
    preview_parser = subparsers.add_parser("preview", help="Podgląd znormalizowanego tekstu")
    preview_parser.add_argument("file", type=str, help="Ścieżka do pliku Markdown")
    preview_parser.add_argument("--code-mode", choices=["spoken", "summary", "skip"], default="spoken", help="Tryb czytania kodu")

    # 2. single
    single_parser = subparsers.add_parser("single", help="Konwersja pojedynczej strony na audio")
    single_parser.add_argument("file", type=str, help="Ścieżka do pliku Markdown")
    single_parser.add_argument("-o", "--output", type=str, default=default_audio_dir, help="Katalog wyjściowy audio")
    single_parser.add_argument("--model", type=str, default="k2-fsa/OmniVoice", help="Ścieżka lub nazwa modelu TTS")
    single_parser.add_argument("--voice", type=str, default=None, help="Próbka głosu (.wav)")
    single_parser.add_argument("--temp", type=float, default=0.35, help="Temperatura próbkowania")
    single_parser.add_argument("--cfg", type=float, default=0.7, help="Współczynnik CFG")
    single_parser.add_argument("--exaggeration", type=float, default=0.25, help="Ekspresja głosu")
    single_parser.add_argument("--mock", action="store_true", help="Użyj syntezatora Mock")

    # 3. batch
    batch_parser = subparsers.add_parser("batch", help="Konwersja wielu stron z katalogu")
    batch_parser.add_argument("dir", type=str, default="pages", nargs="?", help="Katalog ze stronami")
    batch_parser.add_argument("-p", "--pattern", type=str, default="page_*.md", help="Wzorzec plików")
    batch_parser.add_argument("-o", "--output", type=str, default=default_audio_dir, help="Katalog wyjściowy audio")
    batch_parser.add_argument("--model", type=str, default="k2-fsa/OmniVoice", help="Ścieżka lub nazwa modelu TTS")
    batch_parser.add_argument("--voice", type=str, default=None, help="Próbka głosu (.wav)")
    batch_parser.add_argument("--temp", type=float, default=0.35, help="Temperatura")
    batch_parser.add_argument("--cfg", type=float, default=0.7, help="CFG")
    batch_parser.add_argument("--exaggeration", type=float, default=0.25, help="Ekspresja")
    batch_parser.add_argument("--mock", action="store_true", help="Użyj syntezatora Mock")
    batch_parser.add_argument("--overwrite", action="store_true", help="Nadpisz istniejące pliki audio")

    # 4. convert
    convert_parser = subparsers.add_parser("convert", help="Konwersja skanów do Markdown")
    convert_parser.add_argument("-i", "--input", type=str, required=True, help="Katalog ze skanami")
    convert_parser.add_argument("-o", "--output", type=str, required=True, help="Folder wyjściowy .md")
    convert_parser.add_argument("--start", type=int, default=None, help="Początkowa strona")
    convert_parser.add_argument("--end", type=int, default=None, help="Końcowa strona")
    convert_parser.add_argument("--overwrite", action="store_true", help="Nadpisz istniejące pliki .md")
    convert_parser.add_argument("--timeout", type=int, default=360, help="Timeout per strona w sekundach")
    convert_parser.add_argument("--batch-size", type=int, default=4, help="Rozmiar partii")

    # 5. books
    books_parser = subparsers.add_parser("books", help="Zarządzanie magazynem książek")
    books_parser.add_argument("action", choices=["list", "info"], default="list", nargs="?", help="Akcja (list/info)")
    books_parser.add_argument("--slug", type=str, default=None, help="Identyfikator książki")

    return parser


def _handle_books(args: argparse.Namespace, book_repo: BookRepositoryProtocol) -> int:
    if args.action == "list":
        books = book_repo.list_books()
        print("\n" + "=" * 80)
        print("📚 UNIWERSALNY MAGAZYN KSIĄŻEK (SINGLE SOURCE OF TRUTH)")
        print("=" * 80)
        for i, b in enumerate(books, 1):
            pdf_str = f"PDF: {b.paths.original_pdf.name}" if b.paths.original_pdf else "PDF: brak"
            print(f"[{i:02d}] {b.title} (slug: {b.slug})")
            print(f"     Autor: {b.metadata.author or 'Nieznany'} | Język: {b.metadata.language} | {pdf_str}")
            print(f"     Lokalizacja: {b.paths.root_dir.name}/")
            print()
        print("=" * 80 + "\n")
        return 0

    if args.action == "info":
        target_slug = args.slug or book_repo.get_active_book().slug
        book = book_repo.get_book(target_slug)
        if not book:
            print(f"❌ Nie znaleziono książki: {target_slug}")
            return 1
        print("\n" + "=" * 80)
        print(f"📖 SZCZEGÓŁY KSIĄŻKI: {book.title}")
        print("=" * 80)
        print(f"Slug:        {book.slug}")
        print(f"Autor:       {book.metadata.author}")
        print(f"Katalog:     {book.paths.root_dir}")
        print("=" * 80 + "\n")
        return 0
    return 0


def _handle_preview(args: argparse.Namespace, container: ApplicationContainerProtocol) -> int:
    uc_preview = container.create_preview_page_use_case(code_mode=args.code_mode)
    query = PreviewPageQuery(markdown_path=Path(args.file), code_mode=args.code_mode)
    result = uc_preview.execute(query)

    print("\n" + "=" * 80)
    print(f"PODGLĄD NORMALIZACJI DLA PLIKU: {args.file}")
    print("=" * 80 + "\n")
    print(f"Segmenty: {result.segment_count} (PL: {result.pl_segments_count}, EN: {result.en_segments_count}) | Znaki: {result.total_chars} | Słowa: {result.total_words}\n")
    print(result.formatted_preview)
    print("\n" + "=" * 80)
    return 0


def _handle_single(args: argparse.Namespace, container: ApplicationContainerProtocol) -> int:
    engine_type = "mock" if args.mock else "universal"
    synthesis_cfg = SynthesisConfig(
        temperature=args.temp,
        cfg_weight=args.cfg,
        exaggeration=args.exaggeration,
        reference_voice_path=Path(args.voice) if args.voice else None,
    )
    tts = TTSEngineFactory.create(
        engine_type=engine_type,
        model_name_or_path=args.model,
        reference_voice_path=synthesis_cfg.reference_voice_path,
        config=synthesis_cfg,
        cleaner=container.get_audio_cleaner(),
        cache=container.get_audio_cache(),
    )
    uc_single = container.create_synthesize_page_use_case(tts_engine=tts)
    cmd = SynthesizePageCommand(
        markdown_path=Path(args.file),
        output_dir=Path(args.output),
        skip_existing=False,
        save_normalized_text=True,
    )
    res = uc_single.execute(cmd)
    stats = res.stats
    print(f"\n🎉 Wygenerowano audio: {res.audio_path}")
    print(f"    ⏱️ Czas: {stats.duration_sec:.2f}s | Audio: {stats.audio_duration_sec:.2f}s | RTF: {stats.rtf:.2f}")
    return 0


def _handle_batch(args: argparse.Namespace, container: ApplicationContainerProtocol) -> int:
    engine_type = "mock" if args.mock else "universal"
    synthesis_cfg = SynthesisConfig(
        temperature=args.temp,
        cfg_weight=args.cfg,
        exaggeration=args.exaggeration,
        reference_voice_path=Path(args.voice) if args.voice else None,
    )
    tts = TTSEngineFactory.create(
        engine_type=engine_type,
        model_name_or_path=args.model,
        reference_voice_path=synthesis_cfg.reference_voice_path,
        config=synthesis_cfg,
        cleaner=container.get_audio_cleaner(),
        cache=container.get_audio_cache(),
    )
    uc_single = container.create_synthesize_page_use_case(tts_engine=tts)
    reporter = ConsoleProgressReporter()
    uc_batch = container.create_batch_synthesis_use_case(
        synthesize_page_uc=uc_single,
        progress_reporter=reporter,
    )
    bcmd = BatchSynthesisCommand(
        pages_dir=Path(args.dir),
        output_dir=Path(args.output),
        pattern=args.pattern,
        skip_existing=not args.overwrite,
    )
    results = uc_batch.execute(bcmd)
    print(f"\n🎉 Zakończono syntezę wsadową: przetworzono {len(results)} stron.")
    return 0


def _handle_convert(args: argparse.Namespace, container: ApplicationContainerProtocol) -> int:
    reporter = ConsoleProgressReporter()
    uc_convert = container.create_convert_book_use_case(progress_reporter=reporter)
    ccmd = ConvertBookCommand(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        start_page=args.start,
        end_page=args.end,
        overwrite=args.overwrite,
        timeout_sec=args.timeout,
        batch_size=args.batch_size,
    )
    cres = uc_convert.execute(ccmd)
    print(
        f"\n🎉 Zakończono konwersję: przetworzono {cres.processed_count} stron, "
        f"pominięto {cres.skipped_count} w {cres.duration_sec/60:.1f} minut."
    )
    return 0


def main(
    args_list: Optional[Sequence[str]] = None,
    container: Optional[ApplicationContainerProtocol] = None,
    default_audio_dir: str = "data/audio",
) -> int:
    """Dispatches CLI command with dependency injection."""
    _configure_windows_encoding()
    parser = _build_parser(default_audio_dir=default_audio_dir)
    args = parser.parse_args(args_list)

    if not args.command:
        parser.print_help()
        return 0

    if container is None:
        raise RuntimeError("Błąd architektoniczny: kontener zależności nie został przekazany do CLI main().")

    if args.command == "books":
        return _handle_books(args, container.get_book_repository())
    if args.command == "preview":
        return _handle_preview(args, container)
    if args.command == "single":
        return _handle_single(args, container)
    if args.command == "batch":
        return _handle_batch(args, container)
    if args.command == "convert":
        return _handle_convert(args, container)

    return 0