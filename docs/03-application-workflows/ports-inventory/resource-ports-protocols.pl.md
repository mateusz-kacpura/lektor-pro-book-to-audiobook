# Porty i protokoły zarządzania zasobami obliczeniowymi

## Przegląd

Dokument określa kontrakty portów odpowiedzialnych za arbitraż zasobów sprzętowych oraz cykl życia modeli sztucznej inteligencji. Zdefiniowane w module `lektor.application.ports.resource_ports`, protokoły te umożliwiają realizację wzajemnego wykluczania na karcie graficznej bez ujawniania detali sterowników w warstwie aplikacji.

---

## 1. `AIModelHandleProtocol`

Definiuje interfejs pojedynczego uchwytu kontrolującego model w pamięci:

```python
class AIModelHandleProtocol(Protocol):
    @property
    def slot_id(self) -> ModelSlotId:
        """Logiczny identyfikator slotu (np. SLOT_VISION, SLOT_AUDIO_TTS)."""
        ...

    @property
    def resource_id(self) -> ModelResourceId:
        """Identyfikator zasobu/modelu (np. google/gemma-4-12b, k2-fsa/OmniVoice)."""
        ...

    def load(self) -> None:
        """Ładuje wagi modelu do pamięci GPU lub uruchamia proces serwera."""
        ...

    def unload(self) -> None:
        """Zwalnia pamięć VRAM (zamyka proces serwera lub czyści pamięć PyTorch)."""
        ...

    def is_loaded(self) -> bool:
        """Zwraca True, jeśli model jest załadowany do pamięci i gotowy do pracy."""
        ...

```

---

## 2. `AIModelArbiterProtocol`

Zarządza wzajemnym wykluczaniem oraz wywłaszczaniem modeli na pojedynczym akceleratorze:

```python
class AIModelArbiterProtocol(Protocol):
    def acquire(self, slot_id: ModelSlotId) -> None:
        """
        Dzierżawi akcelerator GPU dla żądanego slotu.
        Jeśli inny model zajmuje pamięć, natychmiast go wyładowuje i czyści VRAM.
        """
        ...

    def release(self, slot_id: ModelSlotId) -> None:
        """Zwalnia zasób dla wskazanego slotu i czyści pamięć GPU."""
        ...

    def release_all(self) -> None:
        """Wyładowuje wszystkie zarejestrowane modele i maksymalizuje wolną pamięć VRAM."""
        ...

    def get_active_slot(self) -> Optional[ModelSlotId]:
        """Zwraca slot aktualnie aktywnego modelu lub None."""
        ...

    def get_vram_snapshot(self) -> VramSnapshot:
        """Odpytuje sterownik o aktualną zajętość pamięci VRAM w megabajtach."""
        ...

```