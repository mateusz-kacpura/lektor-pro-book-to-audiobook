"""
lektor.application.use_cases.batch_synthesis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Batch book synthesis (all pages in directory).
"""

from typing import Optional, Sequence

from ...domain.audio_models import SynthesisResult
from ..dtos import BatchSynthesisCommand, SynthesizePageCommand
from ..ports.storage_ports import PageRepositoryProtocol
from ..ports.telemetry_ports import ProgressReporterProtocol
from .synthesize_page import SynthesizePageUseCase


class BatchSynthesisUseCase:
    """Orchestrates batch synthesis of multiple book pages with progress reporting and statistics."""

    def __init__(
        self,
        synthesize_page_uc: SynthesizePageUseCase,
        page_repository: PageRepositoryProtocol,
        progress_reporter: Optional[ProgressReporterProtocol] = None,
    ) -> None:
        self._synthesize_page_uc = synthesize_page_uc
        self._repo = page_repository
        self._reporter = progress_reporter

    def execute(self, cmd: BatchSynthesisCommand) -> Sequence[SynthesisResult]:
        """Processes all matching pages in the directory."""
        pages = self._repo.list_pages(cmd.pages_dir, pattern=cmd.pattern)
        total_pages = len(pages)
        results: list[SynthesisResult] = []

        for idx, page_path in enumerate(pages, 1):
            if self._reporter and self._reporter.check_cancellation():
                break

            if self._reporter:
                self._reporter.on_page_start(page_path, idx, total_pages)

            page_cmd = SynthesizePageCommand(
                markdown_path=page_path,
                output_dir=cmd.output_dir,
                skip_existing=cmd.skip_existing,
                save_normalized_text=cmd.save_normalized_text,
                audio_format=cmd.audio_format,
                language_pair=cmd.language_pair,
            )

            try:
                res = self._synthesize_page_uc.execute(page_cmd)
                results.append(res)
                if self._reporter:
                    if res.skipped_existing:
                        self._reporter.on_skipped(page_path, "Plik audio już istnieje")
                    else:
                        self._reporter.on_page_complete(res)
            except Exception as e:
                if self._reporter:
                    self._reporter.on_error(page_path, e)
                else:
                    raise

        return results
