"""AI Vision OCR adapter using Gemma / Qwen multimodal models."""

from __future__ import annotations

import base64
import os
import time
from typing import Optional, Sequence

import httpx

from ...application.ports.ocr_ports import (
    VisionApiClientProtocol,
    VisionApiResponse,
    VisionPromptBuilderProtocol,
    VisionTranslatorProtocol,
)
from ...domain.conversion_models import DocumentScan, TranslatedMarkdownPage
from ...domain.languages import language_display_name

DEFAULT_CANDIDATE_URLS: Sequence[str] = (
    "http://127.0.0.1:1234/v1",
    "http://localhost:1234/v1",
    "http://127.0.0.1:11434/v1",
    "http://localhost:11434/v1",
)


def resolve_language_display_name(lang_code_or_name: str) -> str:
    """Returns full language name based on ISO code or passes input name."""
    try:
        return language_display_name(lang_code_or_name)
    except ValueError:
        return lang_code_or_name.strip()


class DefaultVisionPromptBuilder(VisionPromptBuilderProtocol):
    """Universal multilingual prompt generator for AI Vision OCR models."""

    def build_system_prompt(
        self,
        target_language: str = "pl",
        source_language: Optional[str] = None,
    ) -> str:
        target_display = resolve_language_display_name(target_language)
        source_info = f" ze ĹşrĂłdĹ‚owego jÄ™zyka ({source_language})" if source_language else ""

        # Implementation note: see the surrounding code for the behavior described here.
        is_transcription_only = (
            source_language is not None
            and source_language.strip().lower() == target_language.strip().lower()
        )

        if is_transcription_only:
            return (
                "You are an expert technical editor, computer scientist, and high-accuracy OCR engine.\n"
                f"Your task is to transcribe this technical page scan verbatim into clean Markdown in {target_display}:\n"
                "1. NARRATION: Transcribe all textual narrative accurately with high fidelity. Maintain technical terminology.\n"
                "2. SOURCE CODE: Transcribe code blocks (```go, ```python, ```yaml, etc.) exactly as written. Do not modify syntax or comments.\n"
                "3. ARCHITECTURAL FIGURES: Convert flowcharts, architecture diagrams, and block diagrams into valid ```mermaid blocks.\n"
                "4. STRUCTURE: Use Markdown headings (#, ##, ###). Discard running headers, footers, and corner page numbers.\n"
                "5. Return ONLY the formatted Markdown content with no conversational introductions or commentary."
            )

        return (
            "Jesteś wybitnym tłumaczem książek informatycznych, inżynierem systemowym i ekspertem lingwistycznym.\n"
            f"Twoim zadaniem jest przetłumaczenie strony technicznej ze skanu{source_info} na język docelowy: {target_display} "
            "w czystym formacie Markdown:\n"
            f"1. NARRACJA: Przetłumacz tekst ciągły na naturalny, płynny i poprawny {target_display}. "
            "Zachowaj oryginalną branżową terminologię inżynierską (np. Kubernetes, Docker, etcd, gRPC, Pod, Goroutine, Channel, Mutex, Circuit Breaker).\n"
            f"2. KOD ŹRÓDŁOWY: Bloki kodu (```go, ```python, ```yaml, itp.) przepisz BEZ ZMIAN składniowych, nazw zmiennych czy sygnatur! "
            f"Przetłumacz WYŁĄCZNIE komentarze wewnątrz kodu na język docelowy ({target_display}).\n"
            "3. SCHEMATY BLOKOWE I ARCHITEKTURA: Wszelkie rysunki, diagramy przepływu oraz architekturę przekształć w poprawny blok ```mermaid (np. flowchart TD, sequenceDiagram).\n"
            "4. HIERARCHIA TEKSTU: Oznacz nagłówki sekcji za pomocą Markdown (#, ##, ###). Odrzuć nagłówki biegowe stron i numery stron w rogach.\n"
            "5. Nie dodawaj żadnych własnych wstępów, uwag ani komentarzy. Zwróć wyłącznie treść przetłumaczonej strony w formacie Markdown."
        )

    def build_user_prompt(
        self,
        target_language: str = "pl",
        source_language: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        target_display = resolve_language_display_name(target_language)
        is_transcription_only = (
            source_language is not None
            and source_language.strip().lower() == target_language.strip().lower()
        )

        if is_transcription_only:
            prompt = (
                f"Dokonaj pe\u0142nego przek\u0142adu tej strony na j\u0119zyk: {target_display} w formacie Markdown. "
                f"Ca\u0142\u0105 narracj\u0119 przet\u0142umacz na naturalny {target_display}. "
                "Bloki kodu \u017ar\u00f3d\u0142owego zachowaj bez zmian sk\u0142adniowych, a rysunki i diagramy przekszta\u0142\u0107 w blok \x60\x60\x60mermaid. "
                "Odrzu\u0107 nag\u0142\u00f3wki biegowe i numery stron w rogach. "
                "Zwr\u00f3\u0107 wy\u0142\u0105cznie tre\u015b\u0107 w formacie Markdown:"
            )
        else:
            prompt = (
                f"Dokonaj pe\u0142nego przek\u0142adu tej strony na j\u0119zyk: {target_display} w formacie Markdown. "
                f"Ca\u0142\u0105 narracj\u0119 przet\u0142umacz na naturalny {target_display}. "
                "Bloki kodu \u017ar\u00f3d\u0142owego zachowaj bez zmian sk\u0142adniowych, a rysunki i diagramy przekszta\u0142\u0107 w blok \x60\x60\x60mermaid. "
                "Odrzu\u0107 nag\u0142\u00f3wki biegowe i numery stron w rogach. "
                "Zwr\u00f3\u0107 wy\u0142\u0105cznie tre\u015b\u0107 w formacie Markdown:"
            )

        if custom_instructions and custom_instructions.strip():
            prompt += f"\n\nInstrukcje dodatkowe: {custom_instructions.strip()}"
        return prompt


class OpenAiVisionHttpClient(VisionApiClientProtocol):
    """HTTP client communicating with OpenAI-compatible vision server."""

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_sec: float = 300.0,
    ) -> None:
        self._configured_url: Optional[str] = api_base_url or os.environ.get("LEKTOR_VISION_API_URL")
        self._model_name: str = model_name or os.environ.get("LEKTOR_VISION_MODEL") or "google/gemma-4-12b"
        self._timeout_sec: float = timeout_sec
        self._resolved_base_url: Optional[str] = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def timeout_sec(self) -> float:
        return self._timeout_sec

    def _resolve_base_url(self) -> str:
        if self._resolved_base_url:
            return self._resolved_base_url
        if self._configured_url:
            self._resolved_base_url = self._configured_url.rstrip("/")
            return self._resolved_base_url

        for url in DEFAULT_CANDIDATE_URLS:
            try:
                with httpx.Client(timeout=0.6) as client:
                    resp = client.get(f"{url}/models")
                    if resp.status_code in (200, 404, 405):
                        self._resolved_base_url = url
                        return url
            except Exception:
                continue

        self._resolved_base_url = "http://127.0.0.1:1234/v1"
        return self._resolved_base_url

    def _resolve_model_id(self, base_url: str) -> str:
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(f"{base_url}/models")
                if resp.status_code == 200:
                    data = resp.json()
                    raw_list = data.get("data", [])
                    models: list[str] = [
                        str(m.get("id", "")) for m in raw_list if isinstance(m, dict) and "id" in m
                    ]
                    if self._model_name in models:
                        return self._model_name
                    req_lower = self._model_name.lower()
                    for m_id in models:
                        if req_lower in m_id.lower() or m_id.lower() in req_lower:
                            return m_id
                    for m_id in models:
                        m_low = m_id.lower()
                        if "gemma-4" in m_low or "gemma" in m_low:
                            return m_id
                        if "vision" in m_low or ("qwen" in m_low and "vl" in m_low):
                            return m_id
        except Exception:
            pass
        return self._model_name

    def send_vision_request(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> VisionApiResponse:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        base_url = self._resolve_base_url()
        active_model = self._resolve_model_id(base_url)

        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    ],
                },
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        req_start = time.perf_counter()
        try:
            with httpx.Client(timeout=self._timeout_sec) as client:
                resp = client.post(f"{base_url}/chat/completions", json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Model {self._model_name} pod adresem {base_url} zwrĂłciĹ‚ status {resp.status_code}: {resp.text}"
                    )
                duration = max(time.perf_counter() - req_start, 0.001)
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError(f"Model {self._model_name} zwrĂłciĹ‚ pustÄ… listÄ™ odpowiedzi.")

                msg = choices[0].get("message", {})
                raw_markdown = str(msg.get("content") or "").strip()
                if not raw_markdown:
                    raw_markdown = str(msg.get("reasoning_content") or "").strip()

                if not raw_markdown:
                    raise RuntimeError(f"Model {self._model_name} zwrĂłciĹ‚ pustÄ… treĹ›Ä‡ odpowiedzi.")

                usage = data.get("usage")
                comp_tokens = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
                if comp_tokens <= 0:
                    comp_tokens = int(len(raw_markdown.split()) * 1.33)
                tok_per_sec = round(comp_tokens / duration, 1)

                return VisionApiResponse(
                    raw_content=raw_markdown,
                    tokens_per_sec=tok_per_sec,
                    total_tokens=comp_tokens,
                    duration_sec=round(duration, 2),
                )

        except httpx.ConnectError as err:
            raise RuntimeError(
                f"Nie moĹĽna poĹ‚Ä…czyÄ‡ siÄ™ z modelem {self._model_name} pod adresem {base_url}. "
                f"Upewnij siÄ™, ĹĽe serwer LM Studio lub Ollama z modelem '{self._model_name}' jest aktywny."
            ) from err
        except httpx.TimeoutException as err:
            raise RuntimeError(
                f"Przekroczono limit czasu oczekiwania ({self._timeout_sec}s) na odpowiedĹş modelu {self._model_name}."
            ) from err


class UniversalVisionTranslatorAdapter(VisionTranslatorProtocol):
    """Universal adapter orchestrating page scan analysis and translation."""

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_sec: float = 300.0,
        client: Optional[VisionApiClientProtocol] = None,
        prompt_builder: Optional[VisionPromptBuilderProtocol] = None,
    ) -> None:
        self._prompt_builder: VisionPromptBuilderProtocol = (
            prompt_builder or DefaultVisionPromptBuilder()
        )
        self._client: VisionApiClientProtocol = client or OpenAiVisionHttpClient(
            api_base_url=api_base_url,
            model_name=model_name,
            timeout_sec=timeout_sec,
        )

    @property
    def model_name(self) -> str:
        return self._client.model_name

    def translate_scan(
        self,
        scan: DocumentScan,
        custom_prompt: Optional[str] = None,
        target_language: str = "pl",
        source_language: Optional[str] = None,
    ) -> TranslatedMarkdownPage:
        scan_path = scan.scan_path
        if not scan_path.exists():
            raise FileNotFoundError(f"Skan strony nie istnieje: {scan_path}")

        image_bytes = scan_path.read_bytes()

        sys_prompt = custom_prompt or self._prompt_builder.build_system_prompt(
            target_language=target_language,
            source_language=source_language,
        )
        user_prompt = self._prompt_builder.build_user_prompt(
            target_language=target_language,
            source_language=source_language,
        )

        response = self._client.send_vision_request(
            image_bytes=image_bytes,
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
        )

        return TranslatedMarkdownPage.from_raw_markdown(
            page_number=scan.page_number,
            raw_markdown=response.raw_content,
            tokens_per_sec=response.tokens_per_sec,
        )


VisionTranslatorAdapter = UniversalVisionTranslatorAdapter
GemmaVisionTranslatorAdapter = UniversalVisionTranslatorAdapter
QwenVisionTranslatorAdapter = UniversalVisionTranslatorAdapter

__all__ = [
    "DefaultVisionPromptBuilder",
    "GemmaVisionTranslatorAdapter",
    "OpenAiVisionHttpClient",
    "QwenVisionTranslatorAdapter",
    "UniversalVisionTranslatorAdapter",
    "VisionTranslatorAdapter",
]
