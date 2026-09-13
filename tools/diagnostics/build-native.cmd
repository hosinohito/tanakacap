@echo off
setlocal
cd /d "%~dp0..\.."
if not exist builds\diagnostics mkdir builds\diagnostics
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 1
cl /nologo /EHsc /std:c++17 /W4 tools\diagnostics\camera_native.cpp /Fo:builds\diagnostics\camera_native.obj /Fe:builds\diagnostics\camera_native.exe /link mfplat.lib mf.lib mfreadwrite.lib mfuuid.lib ole32.lib strmiids.lib ksuser.lib
exit /b %errorlevel%
