from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Product
from .serializers import RegisterSerializer, LoginSerializer, ProductSerializer

User = get_user_model()
signer = TimestampSigner()

class RegisterView(APIView):
    """
    Ендпоінт для реєстрації користувача.
    Надсилає лист із токеном підтвердження на email.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Створення підписаного токена на основі email
            token = signer.sign(user.email)
            
            # Створення посилання для активації пошти
            verification_url = f"{request.scheme}://{request.get_host()}/api/auth/verify-email/?token={token}"
            
            subject = "Підтвердження реєстрації — 3D Store"
            message = (
                f"Вітаємо, {user.first_name or 'користувачу'}!\n\n"
                "Дякуємо за реєстрацію в нашому інтернет-магазині 3D-друкованих фігурок.\n"
                "Щоб завершити реєстрацію та підтвердити email, перейдіть за посиланням нижче:\n"
                f"{verification_url}\n\n"
                "Це посилання дійсне протягом 24 годин."
            )
            
            # Відправлення листа (у розробці виводиться в консоль)
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                # Обробка помилок надсилання пошти (для стійкості)
                pass

            return Response(
                {
                    "message": "Реєстрація успішна! Лист із посиланням для підтвердження надіслано на вашу пошту (перевірте консоль сервера)."
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    Ендпоінт для верифікації пошти користувача за допомогою токена.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Токен для підтвердження відсутній."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Перевірка підпису токена, максимальний час дії — 24 години (86400 секунд)
            email = signer.unsign(token, max_age=86400)
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                return Response({"message": "Цей email вже підтверджено."}, status=status.HTTP_200_OK)
            
            user.is_email_verified = True
            user.save()
            
            return Response({"message": "Електронну пошту успішно підтверджено! Тепер ви можете увійти."}, status=status.HTTP_200_OK)
            
        except SignatureExpired:
            return Response({"error": "Термін дії посилання закінчився (діє 24 години)."}, status=status.HTTP_400_BAD_REQUEST)
        except (BadSignature, User.DoesNotExist):
            return Response({"error": "Недійсний або пошкоджений токен підтвердження."}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Ендпоінт для входу користувача.
    Повертає DRF Token у разі успішного входу.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "email": user.email,
                    "first_name": user.first_name,
                    "country": user.get_country_display(),
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управління каталогом товарів.
    Перегляд доступний усім. Створення/Редагування/Видалення — тільки для адміністраторів (is_staff).
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
