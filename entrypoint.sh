#!/bin/bash
set -e

# Якщо ми використовуємо Volume (наприклад, /app/data), зробимо симлінк для бази даних і медіа
if [ -d "/app/data" ]; then
    echo "Using persistent volume at /app/data"
    
    # Створюємо потрібні директорії
    mkdir -p /app/data/media
    
    # Створюємо базу даних, якщо її немає
    if [ ! -f /app/data/db.sqlite3 ]; then
        echo "Creating new database in volume..."
        touch /app/data/db.sqlite3
    fi
    
    # Симлінки, щоб Django бачив файли на потрібних місцях
    ln -sf /app/data/db.sqlite3 /app/db.sqlite3
    rm -rf /app/media
    ln -s /app/data/media /app/media
fi

# Запускаємо міграції
echo "Running database migrations..."
python manage.py migrate --noinput

# Запускаємо сервер Daphne (підтримка WebSockets + HTTP)
echo "Starting Daphne server on port ${PORT:-8080}..."
daphne -b :: -p ${PORT:-8080} -v 2 --access-log - store3d.asgi:application
