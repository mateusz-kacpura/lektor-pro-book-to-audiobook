@echo off
chcp 65001 > nul
echo [INFO] Przeladowywanie konfiguracji Nginx...
cd /d "%~dp0..\nginx"
nginx.exe -s reload
echo [OK] Konfiguracja Nginx przeladowana pomyslnie!
echo.
pause
