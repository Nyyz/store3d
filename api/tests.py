from django.urls import reverse
from django.core import mail
from django.core.signing import TimestampSigner
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Product

User = get_user_model()
signer = TimestampSigner()

class AuthenticationTests(APITestCase):
    """
    Тести для логіки реєстрації, підтвердження пошти та входу.
    """
    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.verify_url = reverse('auth_verify_email')
        
        self.user_data = {
            "email": "test@example.com",
            "password": "strong_password_123",
            "password_confirm": "strong_password_123",
            "first_name": "Іван",
            "country": "UA"
        }

    def test_user_registration_sends_email(self):
        # Перевіряємо реєстрацію користувача
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Реєстрація успішна", response.data["message"])

        # Перевіряємо створення користувача
        user = User.objects.get(email=self.user_data["email"])
        self.assertFalse(user.is_email_verified)
        self.assertEqual(user.first_name, "Іван")
        self.assertEqual(user.country, "UA")

        # Перевіряємо, чи надіслано лист
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Підтвердження реєстрації", mail.outbox[0].subject)
        self.assertIn(self.user_data["email"], mail.outbox[0].to)

    def test_email_verification_success(self):
        # Створюємо непідтвердженого користувача
        user = User.objects.create_user(
            email="unverified@example.com",
            password="password123",
            first_name="Ольга",
            is_email_verified=False
        )
        
        # Генеруємо токен
        token = signer.sign(user.email)
        
        # Викликаємо ендпоінт підтвердження
        response = self.client.get(f"{self.verify_url}?token={token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Перевіряємо оновлення статусу
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_email_verification_invalid_token(self):
        response = self.client.get(f"{self.verify_url}?token=invalidtoken123")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_login_fails_for_unverified_user(self):
        # Користувач зареєстрований, але не підтвердив пошту
        User.objects.create_user(
            email="notverified@example.com",
            password="password123",
            is_email_verified=False
        )
        
        # Спроба входу
        login_data = {"email": "notverified@example.com", "password": "password123"}
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Будь ласка, підтвердіть вашу електронну пошту", response.data["non_field_errors"][0])

    def test_login_success_for_verified_user(self):
        # Створюємо підтвердженого користувача
        user = User.objects.create_user(
            email="verified@example.com",
            password="password123",
            is_email_verified=True
        )
        
        login_data = {"email": "verified@example.com", "password": "password123"}
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        
        # Перевіряємо створення токена в БД
        token = Token.objects.get(key=response.data["token"])
        self.assertEqual(token.user, user)


class ProductCatalogTests(APITestCase):
    """
    Тести для доступу до каталогу товарів (ProductViewSet).
    """
    def setUp(self):
        self.product_list_url = reverse('product-list')
        self.product = Product.objects.create(
            name="Фігурка Геральта",
            price=750.00,
            stock=5
        )
        
        # Звичайний користувач
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            is_email_verified=True
        )
        self.user_token = Token.objects.create(user=self.user)
        
        # Адміністратор
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            is_email_verified=True,
            is_staff=True
        )
        self.admin_token = Token.objects.create(user=self.admin)
        
        self.new_product_data = {
            "name": "Фігурка Бетмена",
            "description": "Фігурка Бетмена 3D-друк",
            "price": "950.00",
            "stock": 10
        }

    def test_anonymous_user_can_list_and_retrieve_products(self):
        # Отримання списку товарів без авторизації
        response = self.client.get(self.product_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Фігурка Геральта")

        # Отримання окремого товару
        detail_url = reverse('product-detail', args=[self.product.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Фігурка Геральта")

    def test_anonymous_user_cannot_create_product(self):
        response = self.client.post(self.product_list_url, self.new_product_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create_product(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        response = self.client.post(self.product_list_url, self.new_product_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_can_create_product(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.post(self.product_list_url, self.new_product_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Product.objects.latest('id').name, "Фігурка Бетмена")
        
    def test_admin_user_can_update_and_delete_product(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        detail_url = reverse('product-detail', args=[self.product.id])
        
        # Редагування
        update_data = {"name": "Оновлена фігурка", "price": "800.00", "stock": 3}
        response = self.client.put(detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Оновлена фігурка")
        
        # Видалення
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)
