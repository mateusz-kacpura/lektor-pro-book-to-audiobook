@echo off
chcp 65001 > nul
echo ======================================================
echo    STATUS PROCESU NGINX
echo ======================================================
tasklist /fi "imagename eq nginx.exe"
echo.
echo Test portow:
netstat -ano | findstr ":80 "
netstat -ano | findstr ":8080 "
echo.
echo Twoje adresy IP:
echo   LAN IP:       158.75.88.31
echo   Tailscale IP: 100.100.73.61
echo ======================================================
pause
