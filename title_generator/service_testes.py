from service import TitleData, generate_document

test_data = [
    TitleData(
        institute="Институт информационных технологий",
        work_type="Курсовая работа",
        subject="Разработка программного обеспечения",
        theme="Разработка веб-приложения на FastAPI",
        author="Иванов И.И.",
        group="ИТ-123",
        chief="Петров П.П.",
        post="Преподаватель",
    ),
    TitleData(
        institute="Факультет компьютерных наук",
        work_type="Дипломная работа",
        subject="Машинное обучение",
        theme="Классификация текстов с использованием нейросетей",
        author="Сидорова А.Б.",
        group="КН-401",
        chief="Козлов В.В.",
        post="Старший преподаватель",
    ),
    TitleData(
        institute="Институт прикладной математики",
        work_type="Отчет по практике",
        subject="Программирование",
        theme="Разработка API для мобильного приложения",
        author="Петров Е.М.",
        group="ПМ-215",
        chief="Морозов Д.Л.",
        post="Научный руководитель",
    ),
    TitleData(
        institute="Высшая школа анализа данных",
        work_type="Реферат",
        subject="Искусственный интеллект",
        theme="Этические аспекты ИИ в медицине",
        author="Козлова Н.Р.",
        group="АД-302",
        chief="Смирнов А.И.",
        post="Доцент",
    ),
    TitleData(
        institute="Технический университет",
        work_type="Курсовой проект",
        subject="Информационная безопасность",
        theme="Анализ уязвимостей веб-приложений",
        author="Матвеев К.С.",
        group="ИБ-410",
        chief="Федоров О.В.",
        post="Профессор",
    ),
]

for i, data in enumerate(test_data, 1):
    generate_document(data, f"test_doc_{i}")