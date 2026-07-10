from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Nova Poshta API proxy
    path('api/np/cities/', views.np_search_cities, name='np_search_cities'),
    path('api/np/warehouses/', views.np_search_warehouses, name='np_search_warehouses'),

    # Payment
    path('payment/<int:order_id>/', views.payment_view, name='payment'),
    path('payment/<int:order_id>/process/', views.payment_process, name='payment_process'),
]

