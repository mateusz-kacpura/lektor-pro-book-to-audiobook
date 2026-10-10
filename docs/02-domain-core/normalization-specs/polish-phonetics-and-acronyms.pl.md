# Specyfikacja fonetyki języka polskiego i akronimów branżowych

## Przegląd

Dokument definiuje zasady wymowy skrótów informatycznych, akronimów oraz odmiany gramatycznej zapożyczonych pojęć technicznych. Za poprawną fonetyzację odpowiadają moduły `lektor.domain.normalizers.dictionary` oraz `symbols.py`.

---

## 1. Słownik wymowy akronimów i skrótów IT

Słownik `ACRONYMS` rozwija skróty technologiczne na fonetyczne odpowiedniki stosowane w polskiej mowie branżowej:

| Skrót | Zapis fonetyczny | Kontekst technologiczny |
| :--- | :--- | :--- |
| `gRPC` | `dżi ar pi si` | Protokół wywołań zdalnych |
| `API` / `APIs` | `ej pi aj` / `ej pi ajs` | Interfejs programistyczny aplikacji |
| `k8s` / `K8s` | `Kubernetes` | Orkiestrator kontenerów |
| `CI/CD` | `ciągła integracja i ciągłe wdrażanie` | Automatyzacja wydań |
| `HTTP` / `HTTPS` | `ha te te pe` / `ha te te pe es` | Protokoły sieci WWW |
| `TCP` / `UDP` / `IP` | `te ce pe` / `u de pe` / `aj pi` | Protokoły warstwy sieciowej i transportowej |
| `JSON` / `YAML` | `dżejson` / `jaml` | Formaty serializacji danych |
| `CPU` / `RAM` / `GPU` | `ce pe u` / `ram` / `dżi pi u` | Podzespoły komputerowe |
| `AWS` / `GCP` | `a wu es` / `dżi si pi` | Dostawcy chmury publicznej |
| `URL` / `URI` | `u er el` / `ju ar aj` | Identyfikatory zasobów |
| `SLA` / `SLO` / `SLI` | `es el a` / `es el o` / `es el i` | Metryki niezawodności usług |

---

## 2. Odmiana gramatyczna pojęć technicznych

Zapożyczone pojęcia informatyczne są poddawane polskiej fleksji (`POLISH_TECHNICAL_INFLECTIONS`), co zapewnia naturalne brzmienie wypowiedzi lektora:

```python
POLISH_TECHNICAL_INFLECTIONS = {
    r"\bgoroutine\b": "gorutyna",
    r"\bgoroutines\b": "gorutyny",
    r"\bmutex\b": "miuteks",
    r"\bmutexa\b": "miuteksa",
    r"\bmutexy\b": "miuteksy",
    r"\bmutexów\b": "miuteksów",
    r"\bhashmapa\b": "haszmapa",
    r"\bhashmapy\b": "haszmapy",
}

```

---

## 3. Odczyt adresów sieciowych, plików i poczty elektronicznej

Realizowany przez funkcję `normalize_urls_and_emails` w module `symbols.py`:

* **Adresy poczty elektronicznej**: `kontakt@example.com` $\to$ `kontakt małpa example kropka com`.
* **Odnośniki internetowe**: `https://github.com/golang/go` $\to$ `adres github kropka com ukośnik golang ukośnik go`.
* **Pliki konfiguracyjne i źródłowe**: `go.mod` $\to$ `go kropka mod`, `docker-compose.yml` $\to$ `docker-compose kropka jaml`.
