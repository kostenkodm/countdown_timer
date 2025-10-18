@echo off
setlocal

echo Завантаження обновления...

:: Путь к текущей папке
set "BASE_DIR=%~dp0"

:: Скачиваем архив с GitHub
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/kostenkodm/countdown_timer/archive/refs/heads/main.zip' -OutFile '%BASE_DIR%update.zip'"

:: Разархивируем
powershell -Command "Expand-Archive -Path '%BASE_DIR%update.zip' -DestinationPath '%BASE_DIR%temp_update' -Force"

:: Копируем новые файлы (заменяем старые)
xcopy "%BASE_DIR%temp_update\countdown_timer-main\*" "%BASE_DIR%" /E /Y /I

:: Удаляем временные файлы
rmdir /S /Q "%BASE_DIR%temp_update"
del /Q "%BASE_DIR%update.zip"

echo Обновление завершено. Запускаем таймер...
start "" "%BASE_DIR%timer.exe"
exit
