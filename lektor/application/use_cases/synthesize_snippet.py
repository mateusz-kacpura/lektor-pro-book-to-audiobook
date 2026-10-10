"""
lektor.application.use_cases.synthesize_snippet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Synthesizing arbitrary Markdown text snippet (Markdown Studio / Interview).
Pure data flow orchestration with full Dependency Inversion (DIP).
Strict typing without Any.
"""

from typing import Optional, Sequence

from ...domain.audio_models import AudioBuffer, SpeechSegment
from ...domain.normalization import TextNormalizationService
from ..dtos import SynthesizeSnippetCommand, SynthesizeSnippetResult
from ..ports.audio_ports import (
    AudioCacheProtocol,
    AudioStitcherProtocol,
    TTSEngineProtocol,
)
from ..ports.resource_ports import AIModelArbiterProtocol


class SynthesizeMarkdownSnippetUseCase:
    """Orchestrates converting arbitrary Markdown text into audio with cache support."""

    def __init__(
        self,
        tts_engine: TTSEngineProtocol,
        audio_stitcher: AudioStitcherProtocol,
        normalization_service: TextNormalizationService,
        audio_cache: Optional[AudioCacheProtocol] = None,
        model_arbiter: Optional[AIModelArbiterProtocol] = None,
    ) -> None:
        self._tts_engine = tts_engine
        self._stitcher = audio_stitcher
        self._normalizer = normalization_service
        self._cache = audio_cache
        self._arbiter = model_arbiter

    def execute(self, cmd: SynthesizeSnippetCommand) -> SynthesizeSnippetResult:
        """Executes snippet synthesis and always releases leased GPU model."""
        if self._arbiter is None:
            return self._execute(cmd)

        from ...domain.resource_models import SLOT_AUDIO_TTS

        self._arbiter.acquire(SLOT_AUDIO_TTS)
        try:
            return self._execute(cmd)
        finally:
            self._arbiter.release(SLOT_AUDIO_TTS)

    def _execute(self, cmd: SynthesizeSnippetCommand) -> SynthesizeSnippetResult:
        """Executes actual normalization, synthesis, and audio export workflow."""

        out_path = cmd.output_path

        if not cmd.force and self._stitcher.audio_exists(out_path, min_bytes=1000):
            duration = self._stitcher.get_duration_sec(tuple())
            file_size_kb = self._stitcher.get_file_size_kb(out_path)
            return SynthesizeSnippetResult(
                snippet_id=cmd.snippet_id,
                audio_path=out_path,
                duration_sec=duration,
                file_size_kb=file_size_kb,
                segment_count=0,
                normalized_preview=(),
                skipped_existing=True,
            )

        # 1. Markdown normalization into speech segments
        segments: Sequence[SpeechSegment] = self._normalizer.normalize(cmd.markdown, cmd.language_pair)
        if not segments:
            raise ValueError("Brak wykrytych segmentĂłw mowy po normalizacji tekstu.")

        # Implementation note: see the surrounding code for the behavior described here.
        if not self._tts_engine.is_loaded():
            self._tts_engine.load_model()

        # 3. Segment-by-segment synthesis using cache
        audio_chunks: list[tuple[AudioBuffer | Sequence[float], int]] = []
        normalized_preview: list[str] = []
        voice_str = str(cmd.voice_path) if cmd.voice_path else None

        for seg in segments:
            seg_text = seg.text.strip()
            if not seg_text:
                continue

            normalized_preview.append(f"[{seg.lang.upper()}] {seg_text}")

            cached_chunk: Optional[AudioBuffer] = None
            if self._cache is not None and not cmd.force:
                cached_chunk = self._cache.get(
                    seg_text,
                    lang=seg.lang,
                    voice=voice_str,
                    temperature=cmd.temperature,
                    cfg_weight=cmd.cfg_weight,
                )

            if cached_chunk is not None:
                audio_chunks.append((cached_chunk, seg.pause_after_ms))
            else:
                chunk = self._tts_engine.synthesize_segment(seg_text, lang=seg.lang)
                if len(chunk) > 0:
                    if self._cache is not None:
                        self._cache.put(
                            seg_text,
                            chunk,
                            lang=seg.lang,
                            voice=voice_str,
                            temperature=cmd.temperature,
                            cfg_weight=cmd.cfg_weight,
                        )
                    audio_chunks.append((chunk, seg.pause_after_ms))

        # Implementation note: see the surrounding code for the behavior described here.
        stitched_audio = self._stitcher.stitch_segments(audio_chunks)

        saved_path = self._stitcher.save_audio(stitched_audio, out_path, format=cmd.audio_format)
        duration_sec = self._stitcher.get_duration_sec(stitched_audio)
        file_size_kb = self._stitcher.get_file_size_kb(saved_path)

        return SynthesizeSnippetResult(
            snippet_id=cmd.snippet_id,
            audio_path=saved_path,
            duration_sec=round(duration_sec, 2),
            file_size_kb=file_size_kb,
            segment_count=len(segments),
            normalized_preview=tuple(normalized_preview),
            skipped_existing=False,
        )
