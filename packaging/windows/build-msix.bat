@echo off
REM Build MSIX package for Windows Store
REM Run from the project root directory

cd /d "%~dp0\..\.."
powershell -ExecutionPolicy Bypass -File "packaging\windows\build-msix.ps1" %*
