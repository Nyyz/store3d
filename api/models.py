from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    Кастомний менеджер користувачів, де email є унікальним ідентифікатором
    для автентифікації замість username.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Електронна пошта (email) обовʼязкова'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Кастомна модель користувача, яка використовує email як головний ідентифікатор.
    """
    username = None  # Видаляємо дефолтне поле username
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    
    COUNTRY_CHOICES = [
        ('UA', 'Україна'),
        ('PL', 'Польща'),
        ('DE', 'Німеччина'),
        ('US', 'США'),
        ('GB', 'Великобританія'),
        ('FR', 'Франція'),
        ('IT', 'Італія'),
    ]
    country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        default='UA',
        verbose_name=_('country')
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name=_('email verified')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email та password обов'язкові за замовчуванням

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class Product(models.Model):
    """
    Модель товару (3D-фігурки).
    """
    DEFAULT_DESCRIPTION = (
        "Ексклюзивна колекційна фігурка, виготовлена методом високоточного 3D-друку "
        "з якісного екологічного пластику. Проходить ретельну ручну обробку та деталізацію. "
        "Ідеальний подарунок для гіків та колекціонерів."
    )

    name = models.CharField(max_length=255, verbose_name="Назва")
    description = models.TextField(default=DEFAULT_DESCRIPTION, verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Зображення")
    stock = models.PositiveIntegerField(default=0, verbose_name="Кількість на складі")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата додавання")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ['-created_at']


class Order(models.Model):
    """
    Замовлення від клієнта.
    """
    STATUS_CHOICES = [
        ('new', 'Нове'),
        ('processing', 'Обробляється'),
        ('shipped', 'Відправлено'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Скасовано'),
    ]

    DELIVERY_CHOICES = [
        ('nova_poshta', 'Нова Пошта'),
        ('ppl', 'PPL'),
        ('meest', 'Meest Пошта'),
    ]

    PAYMENT_CHOICES = [
        ('bank', 'Банківський рахунок (IBAN)'),
        ('paypal', 'PayPal'),
        ('card', 'Банківська картка'),
    ]

    user = models.ForeignKey(
        'CustomUser', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='orders',
        verbose_name='Користувач'
    )
    first_name = models.CharField(max_length=150, verbose_name="Ім'я")
    last_name = models.CharField(max_length=150, verbose_name='Прізвище')
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')

    # Служба доставки
    delivery_service = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='nova_poshta',
        verbose_name='Служба доставки'
    )

    # Метод оплати
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='bank',
        verbose_name='Спосіб оплати'
    )

    # Нова Пошта
    np_city = models.CharField(max_length=255, blank=True, default='', verbose_name='Місто (НП)')
    np_city_ref = models.CharField(max_length=36, blank=True, default='', verbose_name='Ref міста')
    np_warehouse = models.CharField(max_length=500, blank=True, default='', verbose_name='Відділення (НП)')
    np_warehouse_ref = models.CharField(max_length=36, blank=True, default='', verbose_name='Ref відділення')

    # PPL
    ppl_city = models.CharField(max_length=255, blank=True, default='', verbose_name='Місто (PPL)')
    ppl_point = models.CharField(max_length=500, blank=True, default='', verbose_name='Пункт видачі (PPL)')

    # Meest
    meest_country = models.CharField(max_length=100, blank=True, default='', verbose_name='Країна (Meest)')
    meest_city = models.CharField(max_length=255, blank=True, default='', verbose_name='Місто (Meest)')
    meest_address = models.CharField(max_length=500, blank=True, default='', verbose_name='Адреса/Відділення (Meest)')

    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Загальна сума')
    comment = models.TextField(blank=True, default='', verbose_name='Коментар')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата замовлення')

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    def __str__(self):
        return f'Замовлення #{self.pk} — {self.first_name} {self.last_name}'


class OrderItem(models.Model):
    """
    Товар у замовленні.
    """
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='Замовлення'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(verbose_name='Кількість')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Ціна за шт.')

    class Meta:
        verbose_name = 'Товар замовлення'
        verbose_name_plural = 'Товари замовлення'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity

