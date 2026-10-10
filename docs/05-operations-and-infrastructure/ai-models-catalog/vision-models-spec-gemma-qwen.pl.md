# Specyfikacja modeli wizyjnych (Gemma 4 i Qwen)

## Przegląd

Dokument zawiera opis modeli multimodalnych wykorzystywanych do analizy skanów stron, tłumaczenia technicznego, zabezpieczania kodu źródłowego oraz ekstrakcji diagramów architektonicznych do składni Mermaid.

---

## 1. Obsługiwane modele multimodalne

### Google DeepMind Gemma 4 12B (Główny model)
- **Identyfikator**: `google/gemma-4-12b`
- **Format**: Kwantyzacja GGUF (`Q4_K_M`) uruchamiana przez `llama-server.exe`.
- **Projektor wizyjny**: `mmproj-gemma-4-12B-it-BF16.gguf`.
- **Okno kontekstu**: 8 192 tokeny.
- **Zużycie pamięci VRAM**: ~7,5 do 8,2 GB przy 99 warstwach przeniesionych do GPU.
- **Zalety**: Dokładne tłumaczenie na techniczny język polski, bezbłędne zachowywanie składni Go, precyzyjne odczytywanie połączeń na diagramach.

### Qwen 2.5 VL 7B (Alternatywny)
- **Identyfikator**: `qwen2.5-vl:7b`
- **Format**: GGUF lub serwer Ollama na porcie 11434.
- **Zużycie pamięci VRAM**: ~5,5 do 6,2 GB.
- **Zalety**: Bardzo wysoka prędkość przetwarzania i skuteczność OCR przy drobnym druku.

---

## 2. Standard promptów translacyjnych

Generowanie zapytań nadzoruje `DefaultVisionPromptBuilder`:

- **Prompt systemowy**: Definiuje rolę tłumacza technicznego, nakazuje pozostawienie kodu w oryginale, wymusza konwersję schematów na bloki ```` ```mermaid ```` oraz nakazuje pomijanie nagłówków biegowych i numeracji stron.
- **Prompt użytkownika**: Przekazuje obraz skanu w rozdzielczości 300 DPI z instrukcją docelową.

---

## 3. Wymagania pamięciowe i kwantyzacja

| Wariant modelu | Kwantyzacja | Rozmiar na dysku | Wymagany wolny VRAM | Warstwy na GPU |
| :--- | :--- | :--- | :--- | :--- |
| Gemma 4 12B | `Q4_K_M` | ~7,2 GB | 10,0 GB | 99 (wszystkie) |
| Qwen 2.5 VL 7B | `Q4_K_M` | ~4,8 GB | 8,0 GB | 99 (wszystkie) |
