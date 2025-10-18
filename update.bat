@echo off
setlocal

echo Check for update...

set "BASE_DIR=%~dp0"

powershell -NoProfile -WindowStyle Hidden -Command "Invoke-WebRequest -Uri 'https://github.com/kostenkodm/countdown_timer/releases/latest/download/timer.zip' -OutFile '%BASE_DIR%update.zip'" >nul 2>&1
powershell -NoProfile -WindowStyle Hidden -Command "Expand-Archive -Path '%BASE_DIR%update.zip' -DestinationPath '%BASE_DIR%temp_update' -Force" >nul 2>&1

xcopy "%BASE_DIR%temp_update\countdown_timer-main\*" "%BASE_DIR%" /E /Y /I >nul

rmdir /S /Q "%BASE_DIR%temp_update"
del /Q "%BASE_DIR%update.zip"

echo Update completed. Starting...
start "" "%BASE_DIR%timer.exe"
exit
