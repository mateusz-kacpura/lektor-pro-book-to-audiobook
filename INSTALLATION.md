# Lektor Pro Installation Guide

## Minimum system requirements

- Windows 10/11 64-bit or Linux x86_64.
- Python 3.14+.
- At least 12 GB of dedicated GPU VRAM.
- 16 GB RAM minimum; 32 GB recommended.
- 30 GB free disk space and internet access.

CPU fallback is suitable for tests, but not normal AI synthesis. GPUs with less than 12 GB VRAM do not meet the minimum requirement.

## Identify the GPU

Windows PowerShell:
    Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion

Linux:
    lspci | grep -i -E "vga|3d|nvidia"
    nvidia-smi

Task Manager > Performance > GPU shows the model and dedicated memory. The nvidia-smi table must show GPU name, driver, and total memory.

## NVIDIA drivers and CUDA

1. Identify the exact GPU model.
2. Download the current NVIDIA Studio or Game Ready driver from NVIDIA.
3. Install it and restart.
4. Verify with nvidia-smi.

The application needs a CUDA-compatible driver and CUDA-enabled PyTorch. A full CUDA Toolkit is only needed for CUDA development or extensions. If required, install the toolkit version compatible with the selected PyTorch build, then verify with nvcc --version. Do not install a random CUDA version.

## Python environment

Windows PowerShell:
    py -3.14 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip setuptools wheel

Linux:
    python3.14 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel

If PowerShell blocks activation, run: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

## PyTorch with CUDA

Use the official PyTorch installation selector for the current command. Example only:
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

Verify:
    python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else ''none'')"

CUDA must be available and the GPU must report at least 12 GiB VRAM.

## Project dependencies

    python -m pip install -r requirements.txt
    python -m pip install -e ".[dev]"

Main packages include NumPy, SoundFile, Num2Words, FastAPI, Uvicorn, Pydantic, Python Multipart, PyMuPDF, HTTPX, mypy, Ruff, pre-commit, and scipy-stubs. PyTorch and model packages are installed separately. On Linux, SoundFile may require libsndfile1.

## Optional model services

Local vision translation can use LM Studio at http://127.0.0.1:1234/v1 or Ollama at http://127.0.0.1:11434/v1. Install one only when needed, download a model that fits the VRAM, and update LEKTOR_VISION_API_URL and LEKTOR_VISION_MODEL in .env.

## Configure and verify

    Copy-Item .env.example .env
    python -c "import fastapi, numpy, fitz, soundfile; print(''Core packages: OK'')"
    python -c "import torch; assert torch.cuda.is_available(); v=torch.cuda.get_device_properties(0).total_memory/1024**3; assert v >= 12, f''Only {v:.1f} GiB VRAM detected''; print(''GPU requirement: OK'')"
    python -m ruff check .
    python -m unittest discover -s tests

Review LEKTOR_DATA_DIR, LEKTOR_ACTIVE_BOOK, LEKTOR_DEVICE, LEKTOR_GUI_HOST, LEKTOR_GUI_PORT, and model settings in .env. Start with python run_gui.py and open http://localhost:7860.

## Troubleshooting

- nvidia-smi unavailable: install the NVIDIA driver, restart, and open a new terminal.
- CUDA unavailable in PyTorch: activate the correct environment and reinstall the matching PyTorch wheel.
- Less than 12 GB VRAM: use CPU mode for tests or a supported smaller model.
- Out of memory: close other GPU applications, reduce model size or batch size, and monitor with nvidia-smi -l 2.
- Port 7860 busy: change LEKTOR_GUI_PORT in .env.
- Model/API errors: check network access, disk space, permissions, and the service URL.

## Checklist

- [ ] GPU identified and has at least 12 GB dedicated VRAM.
- [ ] NVIDIA driver installed and nvidia-smi works.
- [ ] Python 3.14+ environment created.
- [ ] CUDA-enabled PyTorch installed and available.
- [ ] Requirements installed and .env configured.
- [ ] Verification tests pass.


---

## Documentation and License

**Author: Mateusz Kacpura**

This documentation is part of the proprietary Lektor Pro project. Private, personal, and non-commercial use is permitted. Public copying, redistribution, modification, or commercial use requires prior written permission. See the project [LICENSE](LICENSE) file. Third-party software, AI models, and imported book content remain subject to their own licenses.


