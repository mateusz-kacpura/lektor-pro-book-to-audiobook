"""
lektor.application.use_cases.preview_page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Preview of normalized text and statistics prior to audio synthesis.
"""

from typing import Sequence

from ...domain.audio_models import SpeechSegment
from ...domain.normalization import TextNormalizationService
from ..dtos import PreviewPageQuery, PreviewPageResult
from ..ports.storage_ports import PageRepositoryProtocol


class PreviewPageUseCase:
    """
    Returns detailed preview of speech segment partitioning, language detection,
    and character/word metrics without loading heavy TTS models.
    """

    def __init__(
        self,
        page_repository: PageRepositoryProtocol,
        normalization_service: TextNormalizationService,
    ) -> None:
        self._repo = page_repository
        self._normalizer = normalization_service

    def execute(self, query: PreviewPageQuery) -> PreviewPageResult:
        """Generates text preview and segmentation metrics."""
        if query.raw_text is not None:
            text = query.raw_text
        elif query.markdown_path is not None:
            text = self._repo.read_markdown(query.markdown_path)
        else:
            raise ValueError("Wymagane jest podanie markdown_path lub raw_text.")

        # Implementation note: see the surrounding code for the behavior described here.
        segments: Sequence[SpeechSegment] = self._normalizer.normalize(text, query.language_pair)

        total_chars = sum(len(seg.text) for seg in segments)
        total_words = sum(len(seg.text.split()) for seg in segments)
        pl_count = sum(1 for seg in segments if seg.lang == "pl")
        en_count = sum(1 for seg in segments if seg.lang == "en")

        lines: list[str] = []
        for idx, seg in enumerate(segments, 1):
            tag = "[KOD]" if seg.is_code else ("[NAGĹĂ“WEK]" if seg.is_header else "")
            lines.append(
                f"[{idx:02d}][{seg.lang.upper()}][Pauza: {seg.pause_after_ms}ms]{tag} {seg.text}"
            )

        preview_str = "\n".join(lines)

        return PreviewPageResult(
            segments=segments,
            total_chars=total_chars,
            total_words=total_words,
            segment_count=len(segments),
            pl_segments_count=pl_count,
            en_segments_count=en_count,
            formatted_preview=preview_str,
        )
