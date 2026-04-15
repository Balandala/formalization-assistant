FROM python:3.14-slim

WORKDIR /app

COPY ./services/title_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/title_generator /app

COPY ./shared /app/shared

EXPOSE 7777

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7777"]