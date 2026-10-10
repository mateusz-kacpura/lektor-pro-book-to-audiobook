@echo off
chcp 65001 > nul
echo ======================================================
echo    ODBLOKOWYWANIE PORTOW 80 I 8080 W ZAPORZE WINDOWS
echo    (Wymaga uprawnien Administratora)
echo ======================================================
echo.
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [BLAD] Ten skrypt musi byc uruchomiony jako Administrator!
    echo Kliknij prawym przyciskiem myszy na ten plik i wybierz:
    echo "Uruchom jako administrator" ("Run as administrator").
    echo.
    pause
    exit /b 1
)

echo Dodawanie reguly zezwalajacej na ruch przychodzacy dla portow 80 i 8080...
netsh advfirewall firewall delete rule name="Lektor GUI Nginx" >nul 2>&1
netsh advfirewall firewall add rule name="Lektor GUI Nginx" dir=in action=allow protocol=TCP localport=80,8080

echo.
echo [SUKCES] Porty 80 i 8080 zostaly pomyslnie odblokowane w zaporze Windows!
echo Teraz inne urzadzenia w sieci moga bez przeszkod otwierac GUI lektora.
echo.
pause
