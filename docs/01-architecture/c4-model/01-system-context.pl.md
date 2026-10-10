# Kontekst systemu (poziom 1)

## Przegląd

Diagram kontekstu przedstawia granice platformy Lektor Pro na najwyższym poziomie abstrakcji, jej użytkowników oraz integracje zewnętrzne. Aplikacja działa lokalnie na stacji roboczej, realizując pełny potok przetwarzania od surowych skanów książek technicznych do zsyntetyzowanego głosu lektora.

```mermaid
flowchart TB
    classDef person fill:#08427b,stroke:#073b6f,color:#fff,stroke-width:2px;
    classDef internalSystem fill:#1168bd,stroke:#0b4884,color:#fff,stroke-width:2px;
    classDef externalSystem fill:#5a6268,stroke:#343a40,color:#fff,stroke-width:2px;

    user["👤 <b>Inżynier oprogramowania / czytelnik</b><br/><i>[Osoba]</i><br/><br/>Słucha audiobooka, analizuje tekst techniczny,<br/>czyta kod źródłowy i diagramy architektoniczne."]:::person

    lektor["🏛️ <b>Platforma Lektor Pro</b><br/><i>[System informatyczny]</i><br/><br/>Lokalny system konwertujący książki (PDF i skany) na Markdown,<br/>generujący mowę i udostępniający webowy odtwarzacz<br/>oraz edytor Markdown studio."]:::internalSystem

    subgraph ExternalBoundary [" Zewnętrzne integracje i zasoby sprzętowe "]
        direction LR
        visionServer["🧠 <b>Lokalny silnik wizyjny AI</b><br/><i>[System zewnętrzny]</i><br/><br/>Zewnętrzny proces LLM/VLM (np. llama-server z modelem<br/>Gemma 4 lub Qwen2.5-VL kompatybilny z API OpenAI)."]:::externalSystem
        filesystem[("💾 <b>System plików stacji roboczej</b><br/><i>[Magazyn danych / System zewnętrzny]</i><br/><br/>Lokalny magazyn danych: pliki PDF, skany stron,<br/>przetłumaczony Markdown oraz pliki dźwiękowe WAV.")]:::externalSystem
        cuda["⚡ <b>Karta graficzna NVIDIA CUDA</b><br/><i>[Akcelerator sprzętowy]</i><br/><br/>Akcelerator GPU zapewniający moc obliczeniową dla modeli<br/>syntezy mowy PyTorch TTS i inferencji wizyjnej."]:::externalSystem
    end

    user -->|"Steruje odtwarzaczem, zleca konwersję i syntezę<br/><b>[HTTP / CLI]</b>"| lektor
    lektor -->|"Przesyła skany stron i prompty translacyjne<br/><b>[HTTP REST / SSE]</b>"| visionServer
    lektor -->|"Odczytuje skany, zapisuje strony Markdown i pliki audio<br/><b>[Operacje wejścia/wyjścia]</b>"| filesystem
    lektor -->|"Wykonuje syntezę neuronową TTS i odczytuje VRAM<br/><b>[CUDA / PyTorch API]</b>"| cuda
```

## Granice i odpowiedzialności

* **Użytkownik**: Korzysta z systemu przez graficzny interfejs przeglądarkowy na porcie 7860 (lub porcie 80 przez przekierowanie TCP) oraz konsolę CLI.
* **Platforma Lektor Pro**: Centralna jednostka orkiestracji napisana w Pythonie 3.14 w czystej architekturze. Koordynuje konwersję, normalizację tekstu, oczyszczanie sygnału audio oraz arbitraż pamięci karty graficznej.
* **Lokalny silnik wizyjny AI**: Niezależny proces inferencyjny analizujący skany stron i generujący sformatowany tekst w języku polskim z zachowaniem kodu źródłowego i diagramów Mermaid.
* **System plików**: Pojedyncze źródło prawdy zorganizowane w hierarchicznej strukturze katalogów (`data/books/<slug>/`).
* **Karta graficzna NVIDIA CUDA**: Fizyczny zasób obliczeniowy współdzielony naprzemiennie przez modele wizyjne i syntezatory mowy.
