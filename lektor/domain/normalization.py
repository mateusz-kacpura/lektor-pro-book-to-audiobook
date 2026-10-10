"""
lektor.domain.normalization
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Domain Service coordinating Markdown text normalization into speech segments.
Pure business logic — zero disk, network, or ML dependencies.
"""

import re
from typing import Optional

from .audio_models import CodeMode, LanguageMode, SpeechSegment
from .languages import LanguagePair
from .normalizers.code_cleaner import clean_inline_code, process_code_block
from .normalizers.code_explainer_protocol import CodeGrammarExplainerProtocol
from .normalizers.code_explainers import GoCodeGrammarExplainer
from .normalizers.dictionary import apply_pronunciation_rules
from .normalizers.language import detect_language
from .normalizers.markdown import clean_markdown_document, clean_markdown_structure
from .normalizers.numbers import normalize_numbers_and_symbols
from .normalizers.spelling import NumberSpellingProtocol
from .normalizers.symbols import normalize_special_characters


class TextNormalizationService:
    """
    Domain service responsible for partitioning Markdown text into coherent,
    phonetically optimized speech segments (SpeechSegment).
    Supports pluggable code explanation strategies (OCP / DIP).
    """

    def __init__(
        self,
        code_mode: CodeMode = "spoken",
        default_lang: str = "pl",
        language_mode: LanguageMode = "bilingual",
        pause_sentence_ms: int = 350,
        pause_paragraph_ms: int = 650,
        pause_header_ms: int = 800,
        code_explainer: Optional[CodeGrammarExplainerProtocol] = None,
        number_speller: Optional[NumberSpellingProtocol] = None,
    ) -> None:
        self.code_mode = code_mode
        self.default_lang = default_lang
        self.language_mode = language_mode
        self.pause_sentence_ms = pause_sentence_ms
        self.pause_paragraph_ms = pause_paragraph_ms
        self.pause_header_ms = pause_header_ms
        self.code_explainer: CodeGrammarExplainerProtocol = (
            code_explainer if code_explainer is not None else GoCodeGrammarExplainer()
        )
        self.number_speller = number_speller

    def normalize(self, raw_text: str, language_pair: Optional[LanguagePair] = None) -> list[SpeechSegment]:
        """Transforms raw Markdown text into speech segments tagged with language ('pl' or 'en')."""
        doc_cleaned = clean_markdown_document(raw_text)
        if not doc_cleaned.strip():
            return []

        segments: list[SpeechSegment] = []

        # Implementation note: see the surrounding code for the behavior described here.
        code_block_pattern = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)```", re.DOTALL)

        parts: list[tuple[str, str, str]] = []
        last_idx = 0
        for match in code_block_pattern.finditer(doc_cleaned):
            start, end = match.span()
            if start > last_idx:
                parts.append(("text", doc_cleaned[last_idx:start], ""))
            parts.append(("code", match.group(2), match.group(1)))
            last_idx = end
        if last_idx < len(doc_cleaned):
            parts.append(("text", doc_cleaned[last_idx:], ""))

        # Implementation note: see the surrounding code for the behavior described here.
        for part_type, part_content, part_lang in parts:
            if part_type == "code":
                spoken_code = process_code_block(
                    part_content,
                    lang=part_lang,
                    mode=self.code_mode,
                    explainer=self.code_explainer,
                )
                if spoken_code:
                    spoken_code = apply_pronunciation_rules(spoken_code)
                    segments.append(
                        SpeechSegment(
                            text=spoken_code,
                            lang="pl",
                            pause_after_ms=self.pause_paragraph_ms,
                            is_code=True,
                        )
                    )
            else:
                text_segments = self._process_text_part(part_content, language_pair)
                segments.extend(text_segments)

        return segments

    def _process_text_part(self, text: str, language_pair: Optional[LanguagePair] = None) -> list[SpeechSegment]:
        """Processes narrative text (paragraphs, headers, lists)."""
        segments: list[SpeechSegment] = []
        paragraphs = text.split("\n\n")

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            is_header = bool(re.match(r"^#{1,6}\s+", p))

            # Implementation note: see the surrounding code for the behavior described here.
            cleaned_p = clean_markdown_structure(p)
            # Implementation note: see the surrounding code for the behavior described here.
            cleaned_p = clean_inline_code(cleaned_p, explainer=self.code_explainer)
            cleaned_p = cleaned_p.strip()

            if not cleaned_p:
                continue

            if is_header:
                pause = self.pause_header_ms
            else:
                pause = self.pause_paragraph_ms

            sub_segments = self._split_paragraph_by_language(cleaned_p, default_pause=pause, language_pair=language_pair)
            for seg in sub_segments:
                if is_header:
                    seg = SpeechSegment(
                        text=seg.text,
                        lang=seg.lang,
                        pause_after_ms=seg.pause_after_ms,
                        is_header=True,
                        is_code=seg.is_code,
                    )
                segments.append(seg)

        return segments

    def _split_paragraph_by_language(
        self,
        paragraph: str,
        default_pause: int,
        language_pair: Optional[LanguagePair] = None,
    ) -> list[SpeechSegment]:
        """Splits paragraph into sentences based on selected language pair."""
        pair = language_pair or LanguagePair.from_legacy_mode(self.language_mode)
        if not pair.is_bilingual:
            cleaned = self._clean_for_language(paragraph, pair.primary)
            return [SpeechSegment(text=cleaned, lang=pair.primary, pause_after_ms=default_pause)] if cleaned else []

        sentences = self._split_into_sentences(paragraph)
        results: list[SpeechSegment] = []
        for index, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            pause = default_pause if index == len(sentences) - 1 else self.pause_sentence_ms
            detected = detect_language(sentence, default_lang=pair.primary)
            secondary = pair.secondary
            if secondary is not None and detected == secondary:
                cleaned = self._clean_for_language(sentence, secondary)
                if cleaned:
                    results.append(SpeechSegment(text=cleaned, lang=secondary, pause_after_ms=pause))
                continue
            if "(" in sentence and ")" in sentence:
                results.extend(self._extract_secondary_bracket_clauses(sentence, pair, pause))
                continue
            cleaned = self._clean_for_language(sentence, pair.primary)
            if cleaned:
                results.append(SpeechSegment(text=cleaned, lang=pair.primary, pause_after_ms=pause))
        return results

    def _extract_secondary_bracket_clauses(
        self,
        sentence: str,
        pair: LanguagePair,
        base_pause: int,
    ) -> list[SpeechSegment]:
        """Splits parenthetical clauses between primary and secondary language."""
        pattern = re.compile(r"\(([^)]+)\)")
        segments: list[SpeechSegment] = []
        last_index = 0
        for match in pattern.finditer(sentence):
            start, end = match.span()
            primary_part = sentence[last_index:start].strip()
            cleaned_primary = self._clean_for_language(primary_part, pair.primary)
            if cleaned_primary:
                segments.append(SpeechSegment(text=cleaned_primary, lang=pair.primary, pause_after_ms=150))

            bracket = match.group(1).strip()
            detected = detect_language(bracket, default_lang=pair.primary)
            secondary = pair.secondary
            bracket_language = secondary if secondary is not None and detected == secondary else pair.primary
            cleaned_bracket = self._clean_for_language(bracket, bracket_language)
            if cleaned_bracket:
                segments.append(SpeechSegment(text=cleaned_bracket, lang=bracket_language, pause_after_ms=150))
            last_index = end

        remaining = sentence[last_index:].strip()
        cleaned_remaining = self._clean_for_language(remaining, pair.primary)
        if cleaned_remaining:
            segments.append(SpeechSegment(text=cleaned_remaining, lang=pair.primary, pause_after_ms=base_pause))
        elif segments:
            last = segments[-1]
            segments[-1] = SpeechSegment(
                text=last.text,
                lang=last.lang,
                pause_after_ms=base_pause,
                is_header=last.is_header,
                is_code=last.is_code,
            )
        return segments

    def _split_into_sentences(self, text: str) -> list[str]:
        """Splits paragraph into sentences."""
        pattern = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄ„Ä†ÄĹĹĂ“ĹšĹąĹ»0-9\"'(\[])")
        raw_splits = pattern.split(text)
        merged: list[str] = []
        for s in raw_splits:
            s_clean = s.strip()
            if not s_clean:
                continue
            if re.search(r"\b(np|itp|itd|tzn|tzw|zob|ok|art|ust|godz|r)\.$", s_clean, re.IGNORECASE):
                if merged:
                    merged[-1] += " " + s_clean
                else:
                    merged.append(s_clean)
            else:
                merged.append(s_clean)
        return merged

    def _clean_for_language(self, text: str, language: str) -> str:
        if language == "pl":
            return self._clean_polish_text(text)
        if language == "en":
            return self._clean_english_text(text)
        return self._clean_generic_text(text)

    def _clean_polish_text(self, text: str) -> str:
        """Comprehensive text cleaning for Polish language."""
        text = normalize_numbers_and_symbols(text)
        text = apply_pronunciation_rules(text)
        text = normalize_special_characters(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _clean_generic_text(self, text: str) -> str:
        """Generic normalization for languages without specific phonetic rules."""
        text = normalize_numbers_and_symbols(text)
        text = normalize_special_characters(text)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_english_text(self, text: str) -> str:
        """Cleans English text segments."""
        text = normalize_special_characters(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
