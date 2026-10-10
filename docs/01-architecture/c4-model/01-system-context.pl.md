# Kontekst systemu (poziom 1)

## Przegląd

Diagram kontekstu przedstawia granice platformy Lektor Pro na najwyższym poziomie abstrakcji, jej użytkowników oraz integracje zewnętrzne. Aplikacja działa lokalnie na stacji roboczej, realizując pełny potok przetwarzania od surowych skanów książek technicznych do zsyntetyzowanego głosu lektora.

```mermaid
C4Context
    title Diagram kontekstu systemu - Lektor Pro

    Person(user, "Inżynier oprogramowania / czytelnik", "Słucha audiobooka, analizuje tekst techniczny, czyta kod i diagramy architektoniczne.")

    System(lektor, "Platforma Lektor Pro", "Lokalny system konwertujący książki (PDF i skany) na format Markdown, generujący mowę i udostępniający odtwarzacz oraz studio.")

    System_Ext(visionServer, "Lokalny silnik wizyjny AI", "Zewnętrzny proces LLM/VLM (np. llama-server z modelem Gemma 4 lub Qwen2.5-VL kompatybilny z API OpenAI).")
    System_Ext(filesystem, "System plików stacji roboczej", "Lokalny magazyn danych: pliki PDF, skany stron, przetłumaczony Markdown oraz pliki dźwiękowe WAV.")
    System_Ext(cuda, "Karta graficzna NVIDIA CUDA", "Akcelerator sprzętowy zapewniający moc obliczeniową dla modeli PyTorch TTS i inferencji wizyjnej.")

    Rel(user, lektor, "Steruje odtwarzaczem, zleca konwersję i syntezę przez przeglądarkę lub CLI", "HTTP / CLI")
    Rel(lektor, filesystem, "Odczytuje skany, zapisuje strony Markdown, pliki audio i metadane", "Operacje wejścia/wyjścia")
    Rel(lektor, visionServer, "Przesyła skany stron i prompty translacyjne", "HTTP REST / SSE")
    Rel(lektor, cuda, "Wykonuje syntezę neuronową PyTorch (OmniVoice/Chatterbox) i odczytuje VRAM", "CUDA / PyTorch API")

```

## Granice i odpowiedzialności

* **Użytkownik**: Korzysta z systemu przez graficzny interfejs przeglądarkowy na porcie 7860 (lub porcie 80 przez przekierowanie TCP) oraz konsolę CLI.
* **Platforma Lektor Pro**: Centralna jednostka orkiestracji napisana w Pythonie 3.14 w czystej architekturze. Koordynuje konwersję, normalizację tekstu, oczyszczanie sygnału audio oraz arbitraż pamięci karty graficznej.
* **Lokalny silnik wizyjny AI**: Niezależny proces inferencyjny analizujący skany stron i generujący sformatowany tekst w języku polskim z zachowaniem kodu źródłowego i diagramów Mermaid.
* **System plików**: Pojedyncze źródło prawdy zorganizowane w strukturze katalogów `data/books/<slug>/`.
* **Karta graficzna NVIDIA CUDA**: Fizyczny zasób obliczeniowy współdzielony naprzemiennie przez modele wizyjne i syntezatory mowy.
iczną strukturą katalogów (`data/books/<slug>/`).

```

---ia.
