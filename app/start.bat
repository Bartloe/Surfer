@echo off
rem start.bat - Surfer-app starten met dubbelklik.
rem Versie 1.0 - 2026-06-30 - draait gui.py met de eigen venv-Python.
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" "gui.py"
