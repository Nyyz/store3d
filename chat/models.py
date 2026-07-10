from django.db import models
from django.conf import settings


class ChatRoom(models.Model):
    """
    Чат-кімната. Одна кімната на кожного клієнта.
    Підтримує як авторизованих користувачів, так і анонімних (через session_key).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Користувач',
        related_name='chat_rooms'
    )
    session_key = models.CharField(
        max_length=40, blank=True, default='',
        verbose_name='Ключ сесії'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    is_active = models.BooleanField(default=True, verbose_name='Активний')

    class Meta:
        verbose_name = 'Чат-кімната'
        verbose_name_plural = 'Чат-кімнати'
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f'Чат: {self.user.email}'
        return f'Чат: анонім ({self.session_key[:8]}...)'

    @property
    def display_name(self):
        if self.user:
            return self.user.first_name or self.user.email
        return f'Гість #{self.pk}'

    @property
    def unread_count(self):
        return self.messages.filter(sender_type='customer', is_read=False).count()

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()


class ChatMessage(models.Model):
    """
    Повідомлення в чаті підтримки.
    """
    SENDER_TYPES = [
        ('customer', 'Клієнт'),
        ('admin', 'Адмін'),
    ]

    room = models.ForeignKey(
        ChatRoom,
        related_name='messages',
        on_delete=models.CASCADE,
        verbose_name='Кімната'
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPES,
        verbose_name='Тип відправника'
    )
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Відправлено')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')

    class Meta:
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.get_sender_type_display()}] {self.text[:50]}'
