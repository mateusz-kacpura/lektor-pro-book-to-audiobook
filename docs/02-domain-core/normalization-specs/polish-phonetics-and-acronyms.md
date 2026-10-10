# Polish phonetics & acronyms specification

## Overview

This specification details the pronunciation rules for IT abbreviations, acronyms, and grammatical inflections of technical terminology. Managed by `lektor.domain.normalizers.dictionary` and `symbols.py`, these mappings ensure acronyms are read with proper industry phonetics.

---

## 1. Technical acronym pronunciation dictionary

The `ACRONYMS` mapping expands uppercase technology abbreviations into phonetic Polish equivalents:

| Abbreviation | Phonetic expansion | Industry context |
| :--- | :--- | :--- |
| `gRPC` | `dżi ar pi si` | Google Remote Procedure Call |
| `API` / `APIs` | `ej pi aj` / `ej pi ajs` | Application Programming Interface |
| `k8s` / `K8s` | `Kubernetes` | Container orchestration |
| `CI/CD` | `ciągła integracja i ciągłe wdrażanie` | Deployment automation |
| `HTTP` / `HTTPS` | `ha te te pe` / `ha te te pe es` | Web transfer protocols |
| `TCP` / `UDP` / `IP` | `te ce pe` / `u de pe` / `aj pi` | Network layer protocols |
| `JSON` / `YAML` | `dżejson` / `jaml` | Data serialization formats |
| `CPU` / `RAM` / `GPU` | `ce pe u` / `ram` / `dżi pi u` | Hardware components |
| `AWS` / `GCP` | `a wu es` / `dżi si pi` | Cloud service providers |
| `URL` / `URI` | `u er el` / `ju ar aj` | Resource identifiers |
| `SLA` / `SLO` / `SLI` | `es el a` / `es el o` / `es el i` | Reliability metrics |

---

## 2. Polish grammatical inflections for technical terms

Foreign computing nouns are adapted into Polish inflected forms (`POLISH_TECHNICAL_INFLECTIONS`) to prevent grammatical friction:

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

## 3. URLs, file extensions & email verbalization

Handled by `normalize_urls_and_emails` in `symbols.py`:

* **Email addresses**: `contact@example.com` $\to$ `contact małpa example kropka com`.
* **Web links**: `https://github.com/golang/go` $\to$ `adres github kropka com ukośnik golang ukośnik go`.
* **Configuration files**: `go.mod` $\to$ `go kropka mod`, `docker-compose.yml` $\to$ `docker-compose kropka jaml`.
