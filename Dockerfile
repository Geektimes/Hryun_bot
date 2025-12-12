# ИЗМЕНЕНИЕ: Используем Python 3.13 согласно requires-python в pyproject.toml
FROM python:3.13-slim

# Настройки для Python и Poetry, чтобы логи не буферизировались
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.1.2

# Устанавливаем рабочую директорию
WORKDIR /app

# ИЗМЕНЕНИЕ: Устанавливаем Poetry через pip
RUN pip install "poetry==$POETRY_VERSION"

# ИЗМЕНЕНИЕ: Сначала копируем только файлы зависимостей (для кэширования слоев Docker)
COPY pyproject.toml poetry.lock ./

# ИЗМЕНЕНИЕ: Настраиваем poetry (не создавать venv) и устанавливаем зависимости
# --no-root означает, что мы не устанавливаем сам наш проект как пакет
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копируем весь код приложения
COPY . .

# Создаем директорию для логов (если её нет)
RUN mkdir -p /app/logs

# Команда для запуска (так как virtualenvs.create false, библиотеки доступны глобально)
CMD ["python", "bot.py"]