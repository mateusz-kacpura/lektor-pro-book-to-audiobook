"""Testy wyboru języka wejściowego w generatorze książki."""

from fastapi import HTTPException

from lektor.adapters.gui.routers.generator import _language_pair_from_params
from lektor.adapters.gui.schemas import GenerationParams


def test_selected_input_language_becomes_single_language_pair() -> None:
    pair = _language_pair_from_params(GenerationParams(input_language="de"))

    assert pair is not None
    assert pair.primary == "de"
    assert pair.secondary is None


def test_automatic_input_language_preserves_legacy_bilingual_mode() -> None:
    pair = _language_pair_from_params(GenerationParams(input_language="auto"))

    assert pair is None


def test_invalid_input_language_is_rejected_before_background_job() -> None:
    try:
        _language_pair_from_params(GenerationParams(input_language="__custom__"))
    except HTTPException as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("Nieprawidłowy kod języka powinien zostać odrzucony")
