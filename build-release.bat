@echo off
setlocal
cd /d "%~dp0"
where pwsh.exe >nul 2>nul
if errorlevel 1 (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-release.ps1" %*
) else (
  pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-release.ps1" %*
)
set "build_result=%errorlevel%"
echo.
if "%build_result%"=="0" (echo Build completed.) else (echo Build failed. See the message and log above.)
pause
exit /b %build_result%
