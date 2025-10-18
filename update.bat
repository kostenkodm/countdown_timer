@echo off
setlocal

echo ������ ����������...

:: ���� � ������� �����
set "BASE_DIR=%~dp0"

:: ��������� ����� � GitHub
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/kostenkodm/countdown_timer/releases/latest/download/timer.zip' -OutFile '%BASE_DIR%update.zip'"

:: �������������
powershell -Command "Expand-Archive -Path '%BASE_DIR%update.zip' -DestinationPath '%BASE_DIR%temp_update' -Force"

:: �������� ����� ����� (�������� ������)
xcopy "%BASE_DIR%temp_update\countdown_timer-main\*" "%BASE_DIR%" /E /Y /I

:: ������� ��������� �����
rmdir /S /Q "%BASE_DIR%temp_update"
del /Q "%BASE_DIR%update.zip"

echo ���������� ���������. ��������� ������...
start "" "%BASE_DIR%timer.exe"
exit
