# Чтобы запустить:

 Открыть командную строку в корне проекта и вписать следующие команды:

## Создать venv и установить зависимости
` python -m venv .venv
  .\.venv\Scripts\activate
  pip install -r requirements.txt `

## Запустить **startup.bat** или:
` start dotnet run enviroment=development --project .\app\backend\csharp_backend\csharp_backend.csproj
 .venv\Scripts\python.exe -m uvicorn app.backend.server.main:app `