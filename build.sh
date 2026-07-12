#!/usr/bin/env bash
# Виходимо з помилкою, якщо будь-яка команда не виконалась
set -o errexit

echo "Встановлюємо залежності..."
pip install -r requirements.txt

echo "Збираємо статику..."
python manage.py collectstatic --noinput

echo "Застосовуємо міграції бази даних..."
python manage.py migrate
