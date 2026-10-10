# ADR-001: Wdrożenie czystej architektury i ścisłej kontroli typów bez użycia Any

## Kontekst
System Lektor Pro integruje zróżnicowane podsystemy: analizę układu dokumentów, multimodalne modele wizyjne (Gemma / Qwen), cyfrowe przetwarzanie sygnałów (DSP), neuronową syntezę mowy (OmniVoice / Chatterbox) oraz strumieniowanie plików. Wczesne implementacje mieszały operacje wejścia/wyjścia bezpośrednio z algorytmami normalizacji tekstu, co uniemożliwiało szybkie testowanie jednostkowe i prowadziło do błędów typowania przy przekazywaniu surowych struktur słownikowych.

## Decyzja
1. **Wdrożenie czystej architektury:** Wprowadzono podział odpowiedzialności na cztery odrębne warstwy:
   - **Domena (`lektor.domain`):** Czyste reguły biznesowe, encje i obiekty wartości. Warstwa w pełni odizolowana od zewnętrznych bibliotek i operacji dyskowych.
   - **Aplikacja (`lektor.application`):** Przypadki użycia (use cases) oraz abstrakcyjne porty wejścia/wyjścia zdefiniowane przez `typing.Protocol`.
   - **Adaptery interfejsów (`lektor.adapters`):** Konkretne implementacje portów: kontrolery FastAPI, interfejs wiersza poleceń, silniki TTS i repozytoria dyskowe.
   - **Infrastruktura (`lektor.infrastructure`):** Konfiguracja sprzętowa, kontener IoC i punkt wejścia aplikacji.
2. **Polityka eliminacji typu Any:**
   - Obowiązuje całkowity zakaz stosowania typu `Any` w kodzie produkcyjnym oraz testach.
   - Wszystkie identyfikatory domenowe są silnie typowane za pomocą `typing.NewType` (`BookSlug`, `PageNumber`, `ConversionTaskId`, `ModelSlotId`).
   - Weryfikator statyczny mypy działa w trybie restrykcyjnym (`warn_return_any = True`, `disallow_untyped_defs = True`).

## Konsekwencje
- **Pozytywne:**
  - Całkowite uniezależnienie logiki przetwarzania od frameworków webowych i bibliotek uczenia maszynowego.
  - Możliwość testowania przypadków użycia w pamięci RAM za pomocą atrap (fakes) w czasie ułamków milisekund.
  - Wykrywanie niespójności interfejsów na etapie statycznej analizy kodu.
- **Negatywne:**
  - Konieczność definiowania dedykowanych struktur DTO oraz formalnych protokołów.