# 🎧 Lektor Pro — Technical Book Reader and TTS Converter

[![Python Version](https://img.shields.io/badge/Python-3.14%2B-blue.svg)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-brightgreen.svg)](GEMINI.md)
[![Typing](https://img.shields.io/badge/Typing-Strict%20(No%20Any)-informational.svg)](references/mypy.ini)
[![Tests](https://img.shields.io/badge/Tests-80%20Passed-success.svg)](tests/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![FastAPI](https://img.shields.io/badge/Web%20GUI-FastAPI-teal.svg)](lektor/adapters/gui/)

Lektor Pro processes technical books from Markdown and scanned PDFs and can generate speech through configurable TTS backends, including an optional Chatterbox Multilingual backend. The project follows Clean Architecture, SOLID principles, and strict static typing without `Any`.

> If Lektor Pro is useful to you, consider starring the repository on GitHub. Stars help me measure interest and prioritize further development.
## Screenshots

Click any thumbnail to open the full-size image.

<table>
  <tr>
    <td><a href="img/%7BA88C501C-5719-4116-A3F4-EDB86BFADF3A%7D.png"><img src="img/%7BA88C501C-5719-4116-A3F4-EDB86BFADF3A%7D.png" alt="Lektor Pro interface" width="400"></a></td>
    <td><a href="img/%7BCE47810E-26C7-430D-9021-6C8CD72866E5%7D.png"><img src="img/%7BCE47810E-26C7-430D-9021-6C8CD72866E5%7D.png" alt="PDF conversion workflow" width="400"></a></td>
  </tr>
  <tr>
    <td><a href="img/%7BD9A15194-D483-48A4-8339-A40D48B4CFBD%7D.png"><img src="img/%7BD9A15194-D483-48A4-8339-A40D48B4CFBD%7D.png" alt="Book and audio management" width="400"></a></td>
    <td><a href="img/%7BF5A8067F-6A8F-4965-A40B-8249AC20109B%7D.png"><img src="img/%7BF5A8067F-6A8F-4965-A40B-8249AC20109B%7D.png" alt="Application dashboard" width="400"></a></td>
  </tr>
</table>

## Features

- **PDF importer and multimodal translator** using PyMuPDF and a configurable vision API/model.
- PDF pages rendered as numbered image scans, with Markdown output and code-block preservation handled by the conversion pipeline.
- Mermaid diagram models and validation within the PDF-to-Markdown conversion workflow.
- Technical glossary protection for Cloud Native terminology.
- Active book switching from the Web GUI without restarting the application.
- Live SSE telemetry with page progress, ETA, GPU VRAM usage, and CUDA utilization.
- Technical text normalization for Go/Python syntax, IT terminology, acronyms, numbers, versions, symbols, and mixed Polish/English text.
- Configurable TTS backends, including Chatterbox Multilingual, with optional voice conditioning, Silero VAD integration, audio cleanup, and synthesis parameters.
- SHA-256 content-addressable audio cache to avoid duplicate synthesis.
- FastAPI Web GUI with an audiobook player, Markdown TTS Studio, interview-practice features, and Arena quiz features.
- Optional LAN and Tailscale access through the included Windows Nginx reverse-proxy configuration.

## Project Architecture

The project follows the Dependency Rule: dependencies point inward, and the domain remains independent of frameworks, databases, and I/O.

```text
data/                         # Application data and generated assets
├── audio_book/               # Shared audio cache, interview, and studio output
├── books/                    # Book-specific scans, pages, audio, images, and translations
└── notes/                    # User notes

lektor/
├── domain/                   # Entities, value objects, business rules, and validation
│   ├── normalizers/          # Text, code, Markdown, and symbol normalizers
│   └── validators/           # Markdown and domain validators
├── application/              # Use cases, DTOs, and application contracts
│   ├── ports/                # Input/output protocols
│   └── use_cases/            # Application workflows
├── adapters/                 # Interface adapters and external integrations
│   ├── audio/                # Audio cleaning and stitching
│   ├── cli/                  # Command-line interface
│   ├── gui/                  # FastAPI Web GUI adapter
│   │   ├── routers/          # Player, converter, studio, notes, and other routes
│   │   ├── schemas/          # Pydantic request and response models
│   │   ├── static/           # CSS, JavaScript, and other static assets
│   │   └── templates/        # HTML templates
│   ├── ocr/                  # PDF splitting, OCR, and vision adapters
│   ├── resources/            # AI model and resource arbitration adapters
│   ├── storage/              # Book, page, notes, and studio repositories
│   ├── text/                 # Text-related interface adapters
│   └── tts/                  # Chatterbox, OmniVoice, mock, and system TTS adapters
└── infrastructure/           # Runtime configuration and dependency composition
    ├── config.py             # Environment and hardware configuration
    ├── container.py          # Dependency-injection composition root
    └── gui_app.py            # FastAPI application assembly

main.py                       # CLI entry point
run_gui.py                    # Web GUI entry point
pyproject.toml                # Project, Ruff, mypy, and dependency configuration
requirements.txt              # Runtime and development dependencies
```

## Quick Start

### Requirements

- Python `3.14+`
- An NVIDIA GPU with CUDA support is recommended; CPU execution is also supported.

### Installation

```bash
pip install -r requirements.txt
# Or install the project in editable/development mode:
pip install -e .
```

Create the environment file from the example:

```bash
cp .env.example .env
```

Important variables include `LEKTOR_DATA_DIR`, `LEKTOR_ACTIVE_BOOK`, `LEKTOR_DEVICE`, `LEKTOR_GUI_HOST`, `LEKTOR_GUI_PORT`, `LEKTOR_AUTO_OPEN_BROWSER`, `LEKTOR_CHATTERBOX_MODEL`, and `LEKTOR_VISION_MODEL`.

## CLI Usage

```bash
# Preview normalized text without generating audio:
python main.py preview data/books/cloud_native_go/pages/page_032.md

# Offline single-page test:
python main.py single data/books/cloud_native_go/pages/page_032.md -o data/audio_book --mock

# Chatterbox synthesis with a reference voice:
python main.py single data/books/cloud_native_go/pages/page_032.md -o data/audio_book --voice data/audio.wav

# Batch-convert a book:
python main.py batch data/books/cloud_native_go/pages/ --pattern "page_*.md" -o data/audio_book

# Manage books:
python main.py books list
python main.py books info --slug cloud-native-in-go

# Convert scanned pages into Markdown:
python main.py convert -i data/books/cloud_native_go/scans -o data/books/cloud_native_go/pages
```

## Nginx Reverse Proxy Configuration

The project uses **Nginx 1.26.2** as a reverse proxy in front of the FastAPI/Uvicorn Web GUI. Nginx is configured in nginx/conf/nginx.conf and forwards requests to the application running on 127.0.0.1:7860.

The configuration:

- listens on HTTP ports 80 and 8080;
- accepts localhost, LAN, VPN, and Tailscale host names;
- forwards the root application and REST API to the FastAPI server;
- forwards /audio/ with buffering disabled, long timeouts, and HTTP Range support for audiobook seeking;
- forwards /static/ and disables aggressive caching during development;
- forwards WebSocket upgrade headers for compatible live connections;
- enables gzip compression for text and SVG responses;
- allows uploads up to 100 MB;
- writes access and error logs to nginx/logs/.

Start the FastAPI application first:

~~~bash
python run_gui.py
~~~

Then start Nginx from the project directory.

### Windows

~~~powershell
.\nginx\nginx.exe -p .\nginx\ -c conf\nginx.conf
~~~

The Web GUI is then available at:

- http://localhost/
- http://localhost:8080/
- http://YOUR_LAN_IP:8080/
- http://YOUR_TAILSCALE_IP:8080/

Useful Windows commands:

~~~powershell
.\nginx\nginx.exe -p .\nginx\ -c conf\nginx.conf -t
.\nginx\nginx.exe -p .\nginx\ -c conf\nginx.conf -s reload
.\nginx\nginx.exe -p .\nginx\ -c conf\nginx.conf -s quit
~~~

For Linux, use the distribution package or an equivalent Nginx installation and copy the same reverse-proxy settings into the system Nginx configuration. Do not expose the service directly to the Internet without authentication, HTTPS, and firewall rules.

The nginx/ directory is ignored by Git because it contains the local Nginx binary, configuration, logs, and temporary runtime files. Recreate or document local configuration separately when deploying to another machine.

## Technical Documentation

The project documentation is built with MkDocs Material and the internationalization plugin configured in mkdocs.yml.

Install the documentation dependencies:

~~~bash
python -m pip install mkdocs-material mkdocs-static-i18n pymdown-extensions
~~~

Start a local development server with live reload:

~~~bash
mkdocs serve
~~~

Open http://127.0.0.1:8000/ in a browser. MkDocs watches the docs/ directory and refreshes the site after Markdown changes.

Build the static documentation site:

~~~bash
mkdocs build --strict
~~~

The generated site is written to site/. To remove the generated output:

~~~bash
Remove-Item -Recurse -Force site
~~~

The documentation supports English and Polish pages according to the language configuration in mkdocs.yml. The project author and copyright information are documented in LICENSE.

## Application Entry Points

The project has two main entry points with different purposes:

### main.py — CLI and batch operations

Use main.py for command-line workflows that do not require the browser interface. It is intended for automation, scripting, previews, single-page synthesis, batch conversion, book management, and PDF import.

Examples:

~~~bash
python main.py preview data/books/cloud_native_go/pages/page_032.md
python main.py single data/books/cloud_native_go/pages/page_032.md -o data/audio_book --mock
python main.py batch data/books/cloud_native_go/pages/ --pattern "page_*.md" -o data/audio_book
python main.py books list
python main.py convert -i data/books/cloud_native_go/scans -o data/books/cloud_native_go/pages
~~~

main.py writes results to the configured data directories and is suitable for shell scripts, scheduled jobs, CI checks, and headless servers.

### run_gui.py — Web interface

Use run_gui.py to start the FastAPI/Uvicorn web application. It provides the browser-based audiobook player, Markdown TTS Studio, interview practice, Arena mode, book switching, and live conversion telemetry.

Start it with:

~~~bash
python run_gui.py
~~~

Then open http://localhost:7860 in a browser. run_gui.py starts the server and connects the Web GUI to the same application services used by the CLI; it does not replace main.py and is not required for command-line or automated workflows.

## Web GUI

Start the application with:

```bash
python run_gui.py
```

The interface is available at `http://localhost:7860` by default. Its main modules are `/` (player), `/studio` (Markdown TTS), `/interview` (technical interview practice), and `/arena` (quiz-based learning).

## Testing and Quality

```bash
python -m unittest discover -s tests
python scripts/run_benchmarks.py
python -m mypy --config-file references/mypy.ini run_gui.py main.py lektor tests scripts
python -m ruff check .
```

The test suite covers unit, integration, end-to-end, and benchmark scenarios, including path-traversal protection, PDF conversion, FastAPI endpoints, audio stitching, memory usage, and GPU telemetry.


## Running the Test Suite

Activate the virtual environment before running tests:

### Linux

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Run all unit, integration, and end-to-end tests:

```bash
python -m unittest discover -s tests -v
```

Run individual test layers when troubleshooting:

```bash
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/integration -v
python -m unittest discover -s tests/e2e -v
```

Run the complete quality checks:

```bash
python -m ruff check .
python -m mypy --config-file references/mypy.ini run_gui.py main.py lektor tests scripts
python scripts/run_benchmarks.py
```

The test suite is designed to run without a GPU. Use the mock TTS engine for CLI checks:

```bash
python main.py single data/books/cloud_native_go/pages/page_032.md -o data/audio_book --mock
```

GPU-dependent synthesis and benchmark checks require a working NVIDIA driver, CUDA-enabled PyTorch, and at least 12 GB of VRAM. Tests that use external model services also require the configured LM Studio or Ollama endpoint.

## CI/CD

Pre-commit hooks are configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml). GitHub Actions configuration is available in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) and validates Python 3.14, mypy, and the test suite on commits and pull requests.

## Installation

See [INSTALLATION.md](INSTALLATION.md) for the complete setup guide.


## Interactive Installers

- Linux: `bash scripts/install_linux.sh` 
- Windows PowerShell: `powershell -ExecutionPolicy Bypass -File scripts/install_windows.ps1` 

Both scripts check Python, NVIDIA drivers, CUDA visibility, and GPU memory, then create `.venv` and install project dependencies.

> Enjoying the project? A GitHub star is a simple way to support its development.

## License and Usage Restrictions

Copyright (c) 2026 **Mateusz Kacpura**. All rights reserved.

See [LICENSE](LICENSE) for the complete terms.

**Author: Mateusz Kacpura**