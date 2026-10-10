# Lektor Pro interactive Windows installer
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvDir = Join-Path $ProjectRoot ".venv"
function Ask([string]$Message) { $answer = Read-Host "$Message [y/N]"; return $answer -match "^(y|yes)$" }
function Info([string]$Message) { Write-Host ""; Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Warn([string]$Message) { Write-Host ""; Write-Host "[WARN] $Message" -ForegroundColor Yellow }
Info "Lektor Pro Windows interactive installer"
Write-Host "Project directory: $ProjectRoot"
Write-Host "Minimum requirement: NVIDIA GPU with at least 12 GiB VRAM."
$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python 3.14+ was not found. Install it from python.org and rerun this script." }
& $python.Source --version
$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) { Info "NVIDIA GPU detected"; & $nvidiaSmi.Source --query-gpu=name,memory.total,driver_version --format=csv,noheader } else { Warn "nvidia-smi was not found. Install the NVIDIA driver before GPU installation."; if (-not (Ask "Continue in CPU/dependency mode?")) { exit 1 } }
$nvcc = Get-Command nvcc -ErrorAction SilentlyContinue
if ($nvcc) { & $nvcc.Source --version } else { Warn "CUDA Toolkit (nvcc) is not installed; PyTorch may still provide its runtime." }
if (-not (Test-Path $VenvDir)) { if (-not (Ask "Create Python virtual environment in .venv?")) { exit 1 }; & $python.Source -m venv $VenvDir }
$venvPython = Join-Path $VenvDir "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip setuptools wheel
if (Ask "Install CUDA-enabled PyTorch?") { Write-Host "Use the current command from https://pytorch.org/get-started/locally/"; $torchCommand = Read-Host "PyTorch install command (leave empty for CPU/default mode)"; if ($torchCommand) { Invoke-Expression $torchCommand } else { & $venvPython -m pip install torch torchvision torchaudio } } else { & $venvPython -m pip install torch torchvision torchaudio }
if (-not (Ask "Install Lektor Pro requirements?")) { exit 1 }
& $venvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if (Ask "Install the project in editable development mode?") { & $venvPython -m pip install -e "$ProjectRoot[dev]" }
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile) -and (Ask "Create .env from .env.example?")) { Copy-Item (Join-Path $ProjectRoot ".env.example") $envFile }
Info "Running verification"
& $venvPython -c "import fastapi,numpy,fitz,soundfile; print(''Core packages: OK'')"
& $venvPython -c "import torch; print(''PyTorch:'',torch.__version__); print(''CUDA available:'',torch.cuda.is_available()); print(''GPU:'',torch.cuda.get_device_name(0) if torch.cuda.is_available() else ''none''); print(''VRAM GiB:'',round(torch.cuda.get_device_properties(0).total_memory/1024**3,2) if torch.cuda.is_available() else 0)"
Write-Host ""; Write-Host "Installation finished." -ForegroundColor Green
Write-Host "Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "Start the GUI with: python run_gui.py"
Write-Host "If Lektor Pro is useful to you, consider starring the project on GitHub: https://github.com/mateusz-kacpura/lektor-pro-book-to-audiobook"
