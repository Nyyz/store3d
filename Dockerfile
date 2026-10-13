FROM python:3.12-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Встановлюємо Python залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код проєкту
COPY . .

# Робимо скрипт запуску виконуваним
RUN chmod +x /app/entrypoint.sh

# Збираємо статичні файли (потрібен тимчасовий SECRET_KEY для build-часу)
RUN SECRET_KEY=build-time-dummy-secret-key \
    DEBUG=False \
    DJANGO_SECURE=False \
    python manage.py collectstatic --noinput

# Відкриваємо порт (Koyeb використовує 8080 за замовчуванням)
EXPOSE 8080

# Запускаємо через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
