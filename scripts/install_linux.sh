#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
echo "Lektor Pro Linux interactive installer"
echo "Minimum requirement: NVIDIA GPU with at least 12 GiB VRAM."
command -v python3 >/dev/null || { echo "Install Python 3.14+ first."; exit 1; }
python3 --version
if command -v nvidia-smi >/dev/null; then nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader; else echo "nvidia-smi not found; install NVIDIA drivers."; fi
if command -v nvcc >/dev/null; then nvcc --version | tail -n 1; else echo "CUDA Toolkit not found; PyTorch may still provide its runtime."; fi
read -r -p "Create/update .venv and install dependencies? [y/N] " a; [[ "${a,,}" == "y" ]] || exit 1
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
echo "Use the current CUDA PyTorch command from https://pytorch.org/get-started/locally/"
read -r -p "PyTorch install command (empty uses default): " t
if [[ -n "$t" ]]; then eval "$t"; else python -m pip install torch torchvision torchaudio; fi
python -m pip install -r "$PROJECT_ROOT/requirements.txt"
if [[ ! -f "$PROJECT_ROOT/.env" ]]; then cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"; fi
python -c "import fastapi,numpy,fitz,soundfile; print(''Core packages: OK'')"
python -c "import torch; print(''CUDA available:'',torch.cuda.is_available()); print(''GPU:'',torch.cuda.get_device_name(0) if torch.cuda.is_available() else ''none'')"
echo "Installation finished. Run: source .venv/bin/activate && python run_gui.py"
echo "If Lektor Pro is useful to you, consider starring the project on GitHub: https://github.com/mateusz-kacpura/lektor-pro-book-to-audiobook"
