C4Component
    title Diagram komponentów - rdzeń aplikacji i adaptery interfejsów

    Container_Boundary(adapters, "Warstwa adapterów interfejsów") {
        Component(guiRouters, "Routery FastAPI", "converter, generator, player, studio, notes, web", "Mapują żądania HTTP na komendy DTO.")
        Component(cliMain, "Punkt wejściowy CLI", "lektor.adapters.cli.main", "Przetwarza argumenty konsoli i wykonuje przypadki użycia.")
        Component(bookRepo, "FileSystemBookRepository", "BookRepositoryProtocol", "Zarządza metadanymi książek, ścieżkami, skanami i stronami.")
        Component(pageRepo, "FileSystemPageRepository", "PageRepositoryProtocol", "Realizuje operacje wejścia/wyjścia dla plików Markdown i stanu.")
        Component(audioCleaner, "SileroAudioCleaner", "AudioCleanerProtocol", "Stosuje filtr Butterwortha, Silero VAD i wygaszanie brzegów.")
        Component(audioStitcher, "NumpyAudioStitcher", "AudioStitcherProtocol", "Łączy bufory próbek, normalizuje głośność i zapisuje WAV.")
        Component(universalTTS, "UniversalTTSEngine", "TTSEngineProtocol", "Koordynuje pracę modeli OmniVoice oraz Chatterbox.")
        Component(visionAdapter, "UniversalVisionTranslatorAdapter", "VisionTranslatorProtocol", "Koduje obrazy, wywołuje API multimodalne i tworzy stronę domenową.")
        Component(pdfSplitter, "PyMuPdfSplitterAdapter", "PdfSplitterProtocol", "Renderuje strony PDF do obrazów JPEG w 300 DPI.")
        Component(arbiter, "DynamicVramModelArbiter", "AIModelArbiterProtocol", "Zarządza wzajemnym wykluczaniem serwera wizyjnego i PyTorch TTS.")
    }

    Container_Boundary(app, "Warstwa przypadków użycia (aplikacja)") {
        Component(ucConvert, "ConvertPdfBookUseCase", "Orkiestrator konwersji", "Koordynuje podział PDF, analizę wizyjną, walidację i telemetrię.")
        Component(ucSynthPage, "SynthesizePageUseCase", "Orkiestrator syntezy", "Koordynuje normalizację, syntezę mowy, łączenie audio i zapis stanu.")
        Component(ucBatchSynth, "BatchSynthesisUseCase", "Przetwarzanie wsadowe", "Iteruje po stronach książki i wykonuje syntezę pojedynczych stron.")
        Component(ucStatus, "GetBookStatusUseCase", "Agregator statusu", "Agreguje całościowy postęp, czas trwania audio i statusy stron.")
    }

    Container_Boundary(domain, "Warstwa encji i reguł (domena)") {
        Component(normalizer, "TextNormalizationService", "Usługa domenowa", "Dzieli tekst, normalizuje liczby, tłumaczy składnię Go i fonetykę.")
        Component(validator, "MarkdownPageValidationService", "Usługa domenowa", "Sprawdza integralność Markdownu, bloków kodu i diagramów Mermaid.")
        Component(glossary, "TechnicalGlossaryService", "Usługa domenowa", "Zabezpiecza pojęcia Cloud Native przed błędnym tłumaczeniem.")
        Component(entities, "Modele domenowe i VO", "Book, ConversionJob, SpeechSegment, DataPaths", "Niezmienne obiekty wartości, encje i maszyny stanów.")
    }

    Rel(guiRouters, ucConvert, "Wywołuje przez obiekt komendy DTO")
    Rel(guiRouters, ucSynthPage, "Wywołuje przez obiekt komendy DTO")
    Rel(guiRouters, ucStatus, "Wywołuje przez obiekt zapytania DTO")
    Rel(cliMain, ucSynthPage, "Wywołuje przez obiekt komendy DTO")
    Rel(cliMain, ucBatchSynth, "Wywołuje przez obiekt komendy DTO")

    Rel(ucConvert, pdfSplitter, "Zleca podział dokumentu")
    Rel(ucConvert, visionAdapter, "Zleca tłumaczenie skanu")
    Rel(ucConvert, arbiter, "Zajmuje slot SLOT_VISION")
    Rel(ucConvert, pageRepo, "Zapisuje plik Markdown")
    Rel(ucConvert, validator, "Weryfikuje integralność wyjścia")
    Rel(ucConvert, glossary, "Chroni terminy techniczne")

    Rel(ucSynthPage, normalizer, "Tworzy segmenty mowy")
    Rel(ucSynthPage, universalTTS, "Generuje próbki audio")
    Rel(ucSynthPage, audioStitcher, "Łączy segmenty i dodaje pauzy")
    Rel(ucSynthPage, pageRepo, "Odczytuje tekst i zapisuje stan")
    Rel(ucSynthPage, arbiter, "Zajmuje slot SLOT_AUDIO_TTS")

    Rel(universalTTS, audioCleaner, "Oczyszcza sygnał mowy")
    Rel(normalizer, entities, "Tworzy instancje SpeechSegment")
    Rel(bookRepo, entities, "Konstruuje encje Book i ścieżki DataPaths")

