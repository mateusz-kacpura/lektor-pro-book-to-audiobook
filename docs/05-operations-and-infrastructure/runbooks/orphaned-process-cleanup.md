# Orphaned process cleanup runbook

## Overview

When the application terminates abnormally, crashes during development, or undergoes an unhandled exception, background subprocesses (`llama-server.exe`) or web servers (`uvicorn`, `nginx.exe`) may remain running in the background. This runbook provides diagnostic commands and termination procedures to release locked TCP ports and graphics memory.

---

## 1. Symptoms & diagnostics

### Locked GPU VRAM
- `nvidia-smi` reports high memory usage (e.g. 7.5 to 8.5 GB VRAM allocated) even though no active translation job is running in Lektor Pro.
- Terminal outputs `CUDA out of memory` during speech synthesis startup.

### Locked TCP ports
- Uvicorn fails with `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 7860): address already in use`.
- Forwarder fails to bind to port 80 or `llama-server.exe` cannot claim port 1234.

---

## 2. Identification commands (PowerShell)

```powershell
# Identify processes occupying project ports (7860, 1234, 80)
Get-NetTCPConnection -LocalPort 7860, 1234, 80 -ErrorAction SilentlyContinue | 
    Select-Object LocalAddress, LocalPort, OwningProcess, State | 
    Format-Table -AutoSize

# Inspect running llama-server instances
Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | 
    Select-Object Id, ProcessName, WorkingSet64, CPU

```

---

## 3. Targeted termination procedures

```powershell
# Terminate orphaned llama-server.exe instances (releases VRAM immediately)
taskkill /F /IM llama-server.exe

# Terminate orphaned Nginx background reverse proxy instances
taskkill /F /IM nginx.exe

# Forcefully stop specific process by PID if port remains locked
Stop-Process -Id <PID> -Force

```

---

## 4. Verification

After executing termination commands, verify GPU state and port clearance:

```powershell
# Check VRAM clearance (expected: free VRAM > 10,000 MB)
nvidia-smi --query-gpu=memory.used,memory.free --format=csv

# Verify port release
Test-NetConnection -ComputerName 127.0.0.1 -Port 7860
```