"""Testy rozszerzonej obslugi jezykow w przeplywie TTS."""

from __future__ import annotations

import numpy as np

from lektor.adapters.gui.schemas import GenerationParams, StudioSynthesizeRequest
from lektor.adapters.tts.backends.chatterbox import ChatterboxBackend
from lektor.adapters.tts.backends.omnivoice import OmniVoiceBackend
from lektor.domain.languages import (
    SUPPORTED_LANGUAGE_CODES,
    LanguagePair,
    is_supported_language,
    language_options,
    normalize_language_code,
    provider_language_code,
)
from lektor.domain.normalization import TextNormalizationService


def test_language_registry_normalizes_iso_variants() -> None:
    assert normalize_language_code(" DE_de ") == "de"
    assert normalize_language_code("  ") == "pl"
    assert is_supported_language("ja-JP")
    assert "pl" in SUPPORTED_LANGUAGE_CODES


def test_normalizer_preserves_selected_non_polish_language() -> None:
    segments = TextNormalizationService(language_mode="de").normalize("Guten Morgen. Das ist ein deutscher Text.")

    assert segments
    assert all(segment.lang == "de" for segment in segments)


def test_bilingual_normalizer_uses_selected_primary_as_fallback() -> None:
    pair = LanguagePair(primary="de", secondary="fr")
    segments = TextNormalizationService(language_mode="bilingual").normalize(
        "Guten Morgen. Das ist ein deutscher Text.",
        language_pair=pair,
    )

    assert segments
    assert all(segment.lang == "de" for segment in segments)


def test_gui_schemas_accept_arbitrary_language_code() -> None:
    assert GenerationParams(language_mode="fr").language_mode == "fr"
    assert GenerationParams(input_language="fr").input_language == "fr"
    assert StudioSynthesizeRequest(markdown="Bonjour", lang="fr").lang == "fr"


def test_omnivoice_backend_forwards_language_code() -> None:
    calls: list[dict[str, object]] = []

    class FakeModel:
        def generate(self, **kwargs: object) -> list[np.ndarray]:
            calls.append(kwargs)
            return [np.zeros(4, dtype=np.float32)]

    backend = OmniVoiceBackend()
    backend._model = FakeModel()
    result = backend.generate("Bonjour", " FR ", None, 1.0, 0.3, 0.7, 0.2, 1.8)

    assert result.dtype == np.float32
    assert calls[0]["language"] == "fr"


def test_chatterbox_backend_forwards_language_code() -> None:
    calls: list[dict[str, object]] = []

    class FakeModel:
        conds = None

        def generate(self, **kwargs: object) -> np.ndarray:
            calls.append(kwargs)
            return np.zeros(4, dtype=np.float32)

    backend = ChatterboxBackend()
    backend._model = FakeModel()
    result = backend.generate("Bonjour", "FR", None, 1.0, 0.3, 0.7, 0.2, 1.8)

    assert result.dtype == np.float32
    assert calls[0]["language_id"] == "fr"


def test_language_pair_has_polish_and_english_defaults() -> None:
    pair = LanguagePair()
    assert pair.primary == "pl"
    assert pair.secondary == "en"
    assert pair.is_bilingual


def test_language_options_are_unique_ordered_and_include_flags() -> None:
    options = language_options()
    codes = [item["code"] for item in options]
    assert len(codes) == len(set(codes))
    assert codes[:10] == ["pl", "en", "de", "es", "fr", "it", "uk", "ja", "zh", "pt"]
    assert options[0]["name"].startswith("\U0001f1f5\U0001f1f1 J\u0119zyk polski (Polish)")
    assert options[-1]["code"] == "__custom__"
    assert options[-1]["custom"] is True


def test_provider_mapping_keeps_model_specific_capabilities() -> None:
    assert provider_language_code("French", "omnivoice") == "fr"
    assert provider_language_code("kbt", "omnivoice") == "kbt"

    import pytest

    with pytest.raises(ValueError, match="nie jest obs\u0142ugiwany"):
        provider_language_code("uk", "chatterbox")
