from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Product

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для реєстрації нових користувачів.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        label="Пароль"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Підтвердження паролю"
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'country', 'password', 'password_confirm']

    def validate(self, data):
        # Перевірка на збіг паролів
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Паролі не співпадають."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            country=validated_data.get('country', 'UA'),
            is_active=True,  # Користувач активний, але не верифікований
            is_email_verified=False
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Серіалізатор для входу користувачів.
    """
    email = serializers.EmailField(label="Email")
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Пароль"
    )

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Необхідно вказати email та пароль.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Неправильний email або пароль.")

        # Перевірка паролю
        if not user.check_password(password):
            raise serializers.ValidationError("Неправильний email або пароль.")

        # Перевірка чи активний акаунт
        if not user.is_active:
            raise serializers.ValidationError("Цей акаунт деактивовано.")

        # Перевірка підтвердження email
        if not user.is_email_verified:
            raise serializers.ValidationError("Будь ласка, підтвердіть вашу електронну пошту перед входом.")

        data['user'] = user
        return data


class ProductSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для товарів (3D-фігурок).
    """
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image', 'stock', 'created_at']
        read_only_fields = ['id', 'created_at']
