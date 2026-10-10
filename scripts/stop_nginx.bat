@echo off
chcp 65001 > nul
echo [INFO] Zatrzymywanie serwera Nginx...
cd /d "%~dp0..\nginx"
nginx.exe -s stop
timeout /t 1 /nobreak > nul
taskkill /f /im nginx.exe 2>nul
echo [OK] Serwer Nginx zostal zatrzymany.
echo.
pause
