@echo off
setlocal
cd /d "%~dp0.."
if not exist tools\bin mkdir tools\bin
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 1
cl /nologo /EHsc /std:c++17 /W4 tools\camera_modes.cpp /Fo:tools\bin\camera_modes.obj /Fe:tools\bin\camera_modes.exe /link mfplat.lib mf.lib mfreadwrite.lib mfuuid.lib ole32.lib
exit /b %errorlevel%
