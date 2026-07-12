#!/usr/bin/env bash
# Виходимо з помилкою, якщо будь-яка команда не виконалась
set -o errexit

echo "Встановлюємо залежності..."
pip install -r requirements.txt

echo "Збираємо статику..."
python manage.py collectstatic --noinput

echo "Застосовуємо міграції бази даних..."
python manage.py migrate

echo "Створюємо суперкористувача (якщо не існує)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
user, created = User.objects.get_or_create(email='admin@example.com');
user.set_password('admin123');
user.is_staff = True;
user.is_superuser = True;
user.save();
print('✅ Admin user ready: admin@example.com / admin123')
"

echo "Додаємо тестові товари (якщо їх ще немає)..."
python manage.py seed_products
