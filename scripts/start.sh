#!/bin/bash
echo "Запуск DocHelper..."

if [ ! -f ".env" ]; then
    echo "Файл .env не найден. Создаю .env.example -> .env"
    cp .env.example .env
fi

docker-compose down --volumes
docker-compose up --build