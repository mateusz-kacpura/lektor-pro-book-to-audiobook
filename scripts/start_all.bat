@echo off
chcp 65001 > nul
echo ======================================================
echo    LEKTOR PRO - START SERWEROW (NGINX + GUI)
echo ======================================================
cd /d "%~dp0.."

REM 1. Start Nginx
cd /d "%~dp0..\nginx"
tasklist /fi "imagename eq nginx.exe" 2>NUL | find /i /n "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Serwer Nginx juz dziala w tle.
) else (
    echo [INFO] Uruchamianie Nginx...
    start "" nginx.exe
)

REM 2. Start GUI
cd /d "%~dp0.."
echo [INFO] Uruchamianie Lektor GUI...
start "Lektor Pro GUI Server" python run_gui.py

echo.
echo ======================================================
echo [SUKCES] Serwery uruchomione!
echo Adresy dostepu:
echo   - Lokalnie:       http://localhost
echo   - Siec LAN:       http://158.75.88.31 (lub port 8080)
echo   - Tailscale VPN:  http://100.100.73.61
echo ======================================================
echo.
timeout /t 3
