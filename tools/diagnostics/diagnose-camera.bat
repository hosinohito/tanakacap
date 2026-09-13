@echo off
cd /d "%~dp0..\.."
".venv\Scripts\python.exe" -X utf8 tools\diagnostics\diagnose_camera.py
pause
