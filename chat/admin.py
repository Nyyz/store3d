from django.contrib import admin
from .models import ChatRoom, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender_type', 'text', 'created_at', 'is_read')
    can_delete = False


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'is_active', 'created_at', 'live_chat_link')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'session_key')
    inlines = [ChatMessageInline]

    def live_chat_link(self, obj):
        from django.utils.html import format_html
        return format_html('<a href="/chat/admin-chat/?room={}" style="background: #7c3aed; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; text-decoration: none;">💬 Live Chat</a>', obj.id)
    live_chat_link.short_description = "Чат"

    def changelist_view(self, request, extra_context=None):
        from django.utils.safestring import mark_safe
        extra_context = extra_context or {}
        extra_context['title'] = mark_safe('Чати &nbsp; <a href="/chat/admin-chat/" style="background: #22c55e; color: white; padding: 6px 12px; border-radius: 4px; font-size: 14px; text-decoration: none; font-weight: bold; margin-left: 10px;">🟢 ВІДКРИТИ ПОВНОЕКРАННИЙ ЧАТ</a>')
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender_type', 'text_short', 'is_read', 'created_at')
    list_filter = ('sender_type', 'is_read', 'created_at')
    readonly_fields = ('room', 'sender_type', 'text', 'created_at')

    def text_short(self, obj):
        return obj.text[:80]
    text_short.short_description = 'Текст'
