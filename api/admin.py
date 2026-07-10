from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Product, Order, OrderItem

class CustomUserAdmin(UserAdmin):
    """
    Налаштування відображення кастомної моделі користувача в панелі адміністратора.
    """
    model = CustomUser
    list_display = ('email', 'first_name', 'country', 'is_email_verified', 'is_staff', 'is_active')
    list_filter = ('is_email_verified', 'is_staff', 'is_active', 'country')
    
    # Використовуємо email замість username для пошуку та сортування
    search_fields = ('email', 'first_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'country')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'country', 'is_email_verified', 'is_active'),
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Налаштування відображення товарів у панелі адміністратора.
    """
    list_display = ('name', 'price', 'stock', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'subtotal_display')
    can_delete = False

    def subtotal_display(self, obj):
        return f'{obj.subtotal} ₴'
    subtotal_display.short_description = 'Сума'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'phone', 'delivery_service', 'payment_method', 'np_city', 'ppl_city', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'delivery_service', 'payment_method', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'np_city', 'ppl_city', 'meest_city')
    readonly_fields = ('created_at', 'total_price')
    inlines = [OrderItemInline]

    fieldsets = (
        ('Клієнт', {'fields': ('user', 'first_name', 'last_name', 'phone', 'email')}),
        ('Спосіб оплати', {'fields': ('payment_method',)}),
        ('Служба доставки', {'fields': ('delivery_service',)}),
        ('Нова Пошта', {'fields': ('np_city', 'np_city_ref', 'np_warehouse', 'np_warehouse_ref'),
                        'classes': ('collapse',)}),
        ('PPL', {'fields': ('ppl_city', 'ppl_point'),
                 'classes': ('collapse',)}),
        ('Meest', {'fields': ('meest_country', 'meest_city', 'meest_address'),
                   'classes': ('collapse',)}),
        ('Замовлення', {'fields': ('total_price', 'comment', 'status', 'created_at')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
