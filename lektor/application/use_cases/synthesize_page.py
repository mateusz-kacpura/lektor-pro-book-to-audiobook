"""
lektor.application.use_cases.synthesize_page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Synthesizing a single Markdown page into an audio file.
Pure data flow orchestration with full Dependency Inversion (DIP).
"""

import time
from typing import Optional, Sequence

from ...domain.audio_models import (
    AudioBuffer,
    SpeechSegment,
    SynthesisResult,
    SynthesisStats,
)
from ...domain.normalization import TextNormalizationService
from ..dtos import SynthesizePageCommand
from ..ports.audio_ports import AudioStitcherProtocol, TTSEngineProtocol
from ..ports.resource_ports import AIModelArbiterProtocol
from ..ports.storage_ports import PageRepositoryProtocol


class SynthesizePageUseCase:
    """Orchestrates the conversion of a Markdown page into an audio file."""

    def __init__(
        self,
        tts_engine: TTSEngineProtocol,
        audio_stitcher: AudioStitcherProtocol,
        page_repository: PageRepositoryProtocol,
        normalization_service: TextNormalizationService,
        model_arbiter: Optional[AIModelArbiterProtocol] = None,
    ) -> None:
        self._tts_engine = tts_engine
        self._stitcher = audio_stitcher
        self._repo = page_repository
        self._normalizer = normalization_service
        self._arbiter = model_arbiter

    def execute(self, cmd: SynthesizePageCommand) -> SynthesisResult:
        """Executes the page synthesis use case."""
        if self._arbiter is not None:
            from ...domain.resource_models import SLOT_AUDIO_TTS

            self._arbiter.acquire(SLOT_AUDIO_TTS)

        md_file = cmd.markdown_path
        out_dir = cmd.output_dir
        out_audio_path = out_dir / f"{md_file.stem}.{cmd.audio_format}"

        # Implementation note: see the surrounding code for the behavior described here.
        if cmd.skip_existing and self._repo.audio_exists(out_audio_path):
            stats = SynthesisStats(
                char_count=0,
                word_count=0,
                segment_count=0,
                duration_sec=0.0,
                audio_duration_sec=0.0,
            )
            return SynthesisResult(
                audio_path=out_audio_path,
                segments=(),
                stats=stats,
                skipped_existing=True,
            )

        # Implementation note: see the surrounding code for the behavior described here.
        raw_markdown = self._repo.read_markdown(md_file)

        # 3. Domain normalization
        segments: Sequence[SpeechSegment] = self._normalizer.normalize(raw_markdown, language_pair=cmd.language_pair)

        total_chars = sum(len(seg.text) for seg in segments)
        total_words = sum(len(seg.text.split()) for seg in segments)

        # Implementation note: see the surrounding code for the behavior described here.
        if cmd.save_normalized_text:
            preview_lines: list[str] = []
            for idx, seg in enumerate(segments, 1):
                preview_lines.append(f"[{idx:02d}][{seg.lang.upper()}][Pauza: {seg.pause_after_ms}ms] {seg.text}")
            preview_content = "\n".join(preview_lines) + "\n"
            preview_path = out_dir / f"{md_file.stem}_normalized.txt"
            self._repo.save_preview(preview_path, preview_content)

        # Implementation note: see the surrounding code for the behavior described here.
        if not segments or total_chars == 0:
            silence = self._stitcher.create_silence(1000)
            saved_path = self._stitcher.save_audio(silence, out_audio_path, format=cmd.audio_format)
            stats = SynthesisStats(
                char_count=0,
                word_count=0,
                segment_count=0,
                duration_sec=0.0,
                audio_duration_sec=1.0,
            )
            return SynthesisResult(
                audio_path=saved_path,
                segments=(),
                stats=stats,
            )

        # Implementation note: see the surrounding code for the behavior described here.
        if not self._tts_engine.is_loaded():
            self._tts_engine.load_model()

        # 7. Segment-by-segment speech synthesis
        audio_chunks: list[tuple[AudioBuffer | Sequence[float], int]] = []
        t0 = time.time()

        for seg in segments:
            chunk = self._tts_engine.synthesize_segment(seg.text, lang=seg.lang)
            audio_chunks.append((chunk, seg.pause_after_ms))

        # Implementation note: see the surrounding code for the behavior described here.
        full_audio = self._stitcher.stitch_segments(audio_chunks)
        saved_path = self._stitcher.save_audio(full_audio, out_audio_path, format=cmd.audio_format)

        generation_sec = time.time() - t0
        audio_duration_sec = self._stitcher.get_duration_sec(full_audio)

        stats = SynthesisStats(
            char_count=total_chars,
            word_count=total_words,
            segment_count=len(segments),
            duration_sec=generation_sec,
            audio_duration_sec=audio_duration_sec,
        )

        # State save
        state_path = out_dir / f"{md_file.stem}_state.json"
        state_dict: dict[str, object] = {
            "status": "completed",
            "page": md_file.stem,
            "char_count": total_chars,
            "duration_sec": generation_sec,
            "audio_duration_sec": audio_duration_sec,
            "rtf": stats.rtf,
            "speed": f"{stats.speed_factor:.2f}x",
        }
        self._repo.save_state(state_path, state_dict)

        return SynthesisResult(
            audio_path=saved_path,
            segments=segments,
            stats=stats,
        )
