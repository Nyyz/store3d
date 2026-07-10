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

# Збираємо статичні файли
RUN python manage.py collectstatic --noinput

# Відкриваємо порт
EXPOSE 8000

# Запускаємо через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
