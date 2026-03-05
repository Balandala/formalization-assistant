# DocHelper — Сервис обработки .docx документов

DocHelper — это веб-приложение на FastAPI, которое:
- Загружает и форматирует .docx файлы.
- Генерирует титульные листы.
- Использует PostgreSQL для хранения метаданных.

## Требования

- [Docker](https://www.docker.com/get-started) (версия 20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (входит в Docker Desktop)
- 2 ГБ свободной памяти

## Быстрый запуск

### 1. Склонируйте репозиторий
    git clone https://github.com/Balandala/formalization-assistant
    cd formalization-assistant

### 2. Создайте `.env` файл, в нем дайте значения переменным POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

### 3. Запустите приложение
#### На Linux/macOS:
```./scripts/start.sh```
**На линуксе может не работать, т.к. не работает `chmod`**
**Выдайте права на исполнение скрипту командой `chmod +x ./scripts/start.sh`**

#### На Windows:
```scripts/start.bat```

## 🔌 Доступ идет по адресу localhost:8000/main

## Остановить приложение можно скриптами:

#### На Linux/macOS:
```./scripts/stop.sh```

#### На Windows:
```scripts/stop.bat```


## Резервное копирование и перенос базы данных

PostgreSQL использует Docker volume `postgres_data`, который хранит данные **независимо от контейнера**.

### Чтобы сделать резервную копию:

```docker exec -t dochelper-postgres-1 pg_dump -U admin dochelper_db > backup.sql```

### Чтобы восстановить:
```cat backup.sql | docker exec -i dochelper-postgres-1 psql -U admin dochelper_db```