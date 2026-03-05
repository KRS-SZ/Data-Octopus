@echo off
:: ============================================================
:: Data Octopus - Windows Installer
:: v5.2.0 - Professional Dashboard mit Manifold Integration
:: ============================================================

echo.
echo  ========================================
echo   DATA OCTOPUS - Installation
echo   Version 5.2.0
echo  ========================================
echo.

:: Check if EXE exists
if exist "DataOctopus.exe" (
    echo [OK] DataOctopus.exe gefunden!
    echo.
    echo Starte Data Octopus...
    start "" "DataOctopus.exe"
    echo.
    echo Die Anwendung wird gestartet.
    echo Dieses Fenster kann geschlossen werden.
) else (
    echo [FEHLER] DataOctopus.exe nicht gefunden!
    echo.
    echo Bitte stelle sicher, dass alle Dateien korrekt kopiert wurden.
    echo.
    pause
)
