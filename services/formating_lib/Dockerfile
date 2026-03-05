FROM python:3.14-slim

WORKDIR /app

COPY ./services/formating_lib/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/formating_lib /app

EXPOSE 7272

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7272"]