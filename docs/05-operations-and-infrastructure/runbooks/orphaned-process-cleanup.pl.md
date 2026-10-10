# Instrukcja czyszczenia osieroconych procesów

## Przegląd

W przypadku awarii, nagłego przerwania pracy w terminalu lub niespodziewanego wyjątku, procesy potomne (`llama-server.exe`) lub serwery sieciowe (`uvicorn`, `nginx.exe`) mogą pozostać aktywne w tle. Instrukcja przedstawia procedury diagnostyczne i polecenia umożliwiające zwolnienie zablokowanych portów TCP oraz pamięci karty graficznej.

---

## 1. Objawy i diagnoza

### Zablokowana pamięć karty graficznej (VRAM)
- Narzędzie `nvidia-smi` raportuje wysoką alokację pamięci (np. 7,5 do 8,5 GB VRAM) mimo braku aktywnego zadania konwersji w aplikacji.
- Terminal zgłasza błąd `CUDA out of memory` podczas próby załadowania silnika syntezy mowy.

### Zablokowane porty sieciowe
- Serwer Uvicorn zgłasza błąd `[Errno 10048] address already in use` przy próbie uruchomienia na porcie 7860.
- Forwarder nie może zająć portu 80 lub `llama-server.exe` nie może wystartować na porcie 1234.

---

## 2. Diagnostyka procesów (PowerShell)

```powershell
# Identyfikacja procesów zajmujących porty aplikacji (7860, 1234, 80)
Get-NetTCPConnection -LocalPort 7860, 1234, 80 -ErrorAction SilentlyContinue | 
    Select-Object LocalAddress, LocalPort, OwningProcess, State | 
    Format-Table -AutoSize

# Sprawdzenie obecności procesu serwera modeli wizyjnych
Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | 
    Select-Object Id, ProcessName, WorkingSet64, CPU

```

---

## 3. Procedury zamykania procesów

```powershell
# Zamykanie osieroconych procesów llama-server.exe (natychmiastowe zwolnienie VRAM)
taskkill /F /IM llama-server.exe

# Zamykanie procesów serwera Nginx w tle
taskkill /F /IM nginx.exe

# Siłowe zamknięcie wybranego procesu po identyfikatorze PID
Stop-Process -Id <PID> -Force

```

---

## 4. Weryfikacja stanu środowiska

Po wykonaniu procedury sprawdź stan karty graficznej oraz dostępność portów:

```powershell
# Weryfikacja wolnej pamięci VRAM (oczekiwana wartość: > 10 000 MB)
nvidia-smi --query-gpu=memory.used,memory.free --format=csv

# Test dostępności portu 7860
Test-NetConnection -ComputerName 127.0.0.1 -Port 7860

```