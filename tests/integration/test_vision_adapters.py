"""
tests.integration.test_vision_adapters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy jednostkowe zrefaktoryzowanych adapterów wizyjnych.
Ścisłe typowanie bez Any.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Optional

from lektor.adapters.ocr.vision_adapter import (
    DefaultVisionPromptBuilder,
    GemmaVisionTranslatorAdapter,
    OpenAiVisionHttpClient,
    QwenVisionTranslatorAdapter,
    UniversalVisionTranslatorAdapter,
    VisionTranslatorAdapter,
)
from lektor.application.ports.ocr_ports import VisionApiClientProtocol, VisionApiResponse
from lektor.domain.conversion_models import DocumentScan, create_page_number


class FakeVisionApiClient(VisionApiClientProtocol):
    """Izolowany fake klienta wizyjnego API na potrzeby testów jednostkowych."""

    def __init__(
        self,
        canned_response: str = "# Przetłumaczona strona\nTreść po polsku.",
        model_name: str = "fake-vision-model",
        tokens_per_sec: float = 33.3,
    ) -> None:
        self._model_name = model_name
        self.canned_response = canned_response
        self.tokens_per_sec = tokens_per_sec
        self.last_image_bytes: Optional[bytes] = None
        self.last_system_prompt: Optional[str] = None
        self.last_user_prompt: Optional[str] = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def send_vision_request(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> VisionApiResponse:
        self.last_image_bytes = image_bytes
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return VisionApiResponse(
            raw_content=self.canned_response,
            tokens_per_sec=self.tokens_per_sec,
            total_tokens=150,
            duration_sec=4.5,
        )


class TestVisionAdapters(unittest.TestCase):
    """Zestaw testów jednostkowych dla architektury adapterów wizyjnych."""

    def test_vision_prompt_builder(self) -> None:
        builder = DefaultVisionPromptBuilder()
        sys_prompt = builder.build_system_prompt(target_language="pl")
        self.assertIn("tłumaczem książek informatycznych", sys_prompt)

        user_prompt = builder.build_user_prompt(target_language="pl")
        self.assertIn("Dokonaj pełnego przekładu", user_prompt)

        custom_user_prompt = builder.build_user_prompt(target_language="pl", custom_instructions="Zachowaj termin Sidecar.")
        self.assertIn("Zachowaj termin Sidecar.", custom_user_prompt)

    def test_qwen_vision_adapter_with_dependency_injection(self) -> None:
        self.assertIs(VisionTranslatorAdapter, UniversalVisionTranslatorAdapter)
        self.assertIs(QwenVisionTranslatorAdapter, UniversalVisionTranslatorAdapter)
        self.assertIs(GemmaVisionTranslatorAdapter, UniversalVisionTranslatorAdapter)

        custom_model_adapter = UniversalVisionTranslatorAdapter(model_name="meta-llama/llama-3.2-11b-vision")
        self.assertEqual(custom_model_adapter.model_name, "meta-llama/llama-3.2-11b-vision")

        fake_client = FakeVisionApiClient(
            canned_response=(
                "# Strona 1\n"
                "Opis architektury.\n"
                "```mermaid\nflowchart LR\nA --> B\n```\n"
                "```go\nvar x int = 10\n```"
            ),
            model_name="google/gemma-4-12b",
            tokens_per_sec=50.0,
        )
        adapter = UniversalVisionTranslatorAdapter(
            client=fake_client,
        )

        self.assertEqual(adapter.model_name, "google/gemma-4-12b")

        missing_scan = DocumentScan(
            page_number=create_page_number(1),
            scan_path=Path("non_existent_file_path.jpg"),
        )
        with self.assertRaises(FileNotFoundError):
            adapter.translate_scan(missing_scan)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"dummy_image_binary_content")
            tmp_path = Path(tmp.name)

        try:
            valid_scan = DocumentScan(
                page_number=create_page_number(1),
                scan_path=tmp_path,
            )
            result = adapter.translate_scan(valid_scan, target_language="pl")

            self.assertEqual(int(result.page_number), 1)
            self.assertEqual(result.tokens_per_sec, 50.0)
            self.assertEqual(len(result.diagrams), 1)
            self.assertEqual(result.diagrams[0].diagram_type, "flowchart")
            self.assertEqual(result.code_blocks_count, 1)

            self.assertEqual(fake_client.last_image_bytes, b"dummy_image_binary_content")
            self.assertIsNotNone(fake_client.last_system_prompt)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_openai_vision_http_client_properties(self) -> None:
        client = OpenAiVisionHttpClient(
            api_base_url="http://127.0.0.1:1234/v1",
            model_name="google/gemma-4-12b",
            timeout_sec=60.0,
        )
        self.assertEqual(client.model_name, "google/gemma-4-12b")
        self.assertEqual(client.timeout_sec, 60.0)
        self.assertEqual(client._resolve_base_url(), "http://127.0.0.1:1234/v1")


if __name__ == "__main__":
    unittest.main()