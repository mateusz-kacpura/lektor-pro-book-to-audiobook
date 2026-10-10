@echo off
chcp 65001 > nul
echo ======================================================
echo    LEKTOR PRO - URUCHAMIANIE SERWERA NGINX
echo ======================================================
cd /d "%~dp0..\nginx"

tasklist /fi "imagename eq nginx.exe" 2>NUL | find /i /n "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Nginx juz dziala w tle!
) else (
    echo [INFO] Startowanie procesu nginx.exe...
    start "" nginx.exe
    timeout /t 1 /nobreak > nul
)

echo.
echo ======================================================
echo [OK] Serwer Nginx jest aktywny!
echo Adresy dostepu z innego komputera w sieci:
echo   - Siec lokalna (LAN):   http://158.75.88.31
echo   - Alternatywny port:    http://158.75.88.31:8080
echo   - Przez Tailscale VPN:  http://100.100.73.61
echo   - Lokalnie:             http://localhost
echo ======================================================
echo.
pause
