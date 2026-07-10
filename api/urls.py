from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, VerifyEmailView, LoginView, ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    # Аутентифікація
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='auth_verify_email'),
    path('auth/login/', LoginView.as_view(), name='auth_login'),
    
    # Каталог товарів та решта API
    path('', include(router.urls)),
]
