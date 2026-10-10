# Oczyszczanie sygnału audio (Silero VAD i potok DSP)

## Przegląd

Adapter `SileroAudioCleaner` (`lektor.adapters.audio.cleaner`) realizuje cyfrowe przetwarzanie sygnałów dźwiękowych wymagane przez regułę `BR-017`. Usuwa dudnienie vocodera, odcina artefakty końca wypowiedzi, redukuje szum tła oraz wygładza krawędzie buforów mowy.

---

## 1. Architektura potoku przetwarzania sygnału

```mermaid
flowchart LR
    Raw[Surowy bufor mowy z TTS] --> HPF[Filtr Butterwortha 75 Hz 4. rzędu]
    HPF --> VAD[Przycięcie granic mowy Silero VAD]
    VAD --> NR[Spektralna redukcja szumów]
    NR --> Fade[Wygładzanie krawędzi 15ms in / 35ms out]
    Fade --> Clean[Oczyszczony bufor AudioBuffer]

```

---

## 2. Etapy przetwarzania sygnału

### Krok 1: Filtr górnoprzepustowy Butterwortha

* **Rząd filtru**: Filtr cyfrowy 4. rzędu o zerowym przesunięciu fazowym (`scipy.signal.filtfilt`).
* **Częstotliwość odcięcia**: $75\text{ Hz}$ przy częstotliwości próbkowania $f_s = 24\,000\text{ Hz}$.
* **Zadanie**: Usuwa składową stałą, przydźwięk sieciowy oraz dudnienie niskich częstotliwości.

### Krok 2: Detekcja aktywności głosu Silero VAD

* **Model neuronowy**: Detektor `silero_vad` uruchamiany przez TorchHub.
* **Próbkowanie**: Wewnętrzna konwersja z $24\text{ kHz}$ do $16\text{ kHz}$ na potrzeby inferencji.
* **Próg czułości**: $\theta = 0{,}45$.
* **Tryb awaryjny**: W przypadku braku detekcji przez VAD system analizuje energię RMS w oknie ostatnich $400\text{ ms}$.
* **Margines bezpieczeństwa**: Pozostawia $100\text{ ms}$ naturalnego wybrzmienia po ostatniej wykrytej sylabie.

### Krok 3: Spektralna redukcja szumów

* **Biblioteka**: `noisereduce.reduce_noise`.
* **Działanie**: Tłumienie stacjonarnego szumu tła i artefaktów vocodera neuronowego.

### Krok 4: Cosinusowe wygładzanie brzegów

Zapobiega trzaskom cyfrowym podczas łączenia segmentów:

* **Wyciszenie narastające (fade-in)**: Rampa liniowa o długości $15\text{ ms}$.
* **Wyciszenie opadające (fade-out)**: Krzywa cosinusowa o długości $35\text{ ms}$:

$$w(t) = \cos^2\left(\frac{\pi t}{2 T_{\text{fade}}}\right), \quad t \in [0, T_{\text{fade}}]$$



---

## 3. Normy wydajnościowe

* Bardzo krótkie segmenty ($\le 0{,}2\text{ s}$) omijają zaawansowane filtry, co zapobiega zniekształceniom krótkich wtrąceń.
* Szczytowe zużycie pamięci sterty podczas filtracji nie przekracza $10\text{ MB}$ na $40\text{ sekund}$ surowego dźwięku.
