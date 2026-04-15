FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-writer \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY ./shared /app/shared
COPY ./app/backend /app/backend
COPY ./app/frontend /app/frontend


RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "backend.server.main:app", "--host", "0.0.0.0", "--port", "8000"]