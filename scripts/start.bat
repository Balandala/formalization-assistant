@echo off
echo Запуск DocHelper...

if not exist ".env" (
    echo Файл .env не найден. Копирую .env.example -> .env
    copy .env.example .env >nul
)

docker-compose down --volumes
docker-compose up --build
pause