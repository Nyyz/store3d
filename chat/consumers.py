import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage


class CustomerChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer для клієнтського чату.
    Кожен клієнт підключається до своєї кімнати.
    """

    async def connect(self):
        self.room = await self._get_or_create_room()
        self.room_group_name = f'chat_{self.room.pk}'

        # Приєднуємося до групи кімнати
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Також приєднуємося до загальної групи адмінів (щоб адмін бачив нові чати)
        await self.channel_layer.group_add(
            'admin_chat_updates',
            self.channel_name
        )

        await self.accept()

        # Надсилаємо історію повідомлень
        messages = await self._get_messages()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages,
            'room_id': self.room.pk,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.channel_layer.group_discard(
                'admin_chat_updates',
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get('message', '').strip()

        if not message_text:
            return

        # Зберігаємо повідомлення в БД
        msg = await self._save_message(message_text, 'customer')

        # Надсилаємо повідомлення в групу кімнати (побачать і клієнт, і адмін)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender_type': 'customer',
                'timestamp': msg.created_at.strftime('%H:%M'),
                'message_id': msg.pk,
            }
        )

        # Сповіщаємо адмінів про нове повідомлення
        await self.channel_layer.group_send(
            'admin_chat_updates',
            {
                'type': 'new_message_notification',
                'room_id': self.room.pk,
                'room_name': await self._get_room_display_name(),
                'message': message_text,
                'sender_type': 'customer',
                'timestamp': msg.created_at.strftime('%H:%M'),
            }
        )

    async def chat_message(self, event):
        """Обробляє повідомлення чату."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_type': event['sender_type'],
            'timestamp': event['timestamp'],
        }))

    async def new_message_notification(self, event):
        """Ігноруємо сповіщення для клієнта."""
        pass

    @database_sync_to_async
    def _get_or_create_room(self):
        user = self.scope.get('user')
        session = self.scope.get('session', {})

        if user and user.is_authenticated:
            room, _ = ChatRoom.objects.get_or_create(
                user=user, is_active=True,
                defaults={'session_key': ''}
            )
        else:
            session_key = session.session_key if hasattr(session, 'session_key') else ''
            if not session_key:
                session_key = 'anon'
            room, _ = ChatRoom.objects.get_or_create(
                session_key=session_key, user=None, is_active=True,
                defaults={}
            )
        return room

    @database_sync_to_async
    def _get_messages(self):
        msgs = self.room.messages.order_by('-created_at')[:50]
        return [
            {
                'message': m.text,
                'sender_type': m.sender_type,
                'timestamp': m.created_at.strftime('%H:%M'),
            }
            for m in reversed(msgs)
        ]

    @database_sync_to_async
    def _save_message(self, text, sender_type):
        return ChatMessage.objects.create(
            room=self.room,
            sender_type=sender_type,
            text=text
        )

    @database_sync_to_async
    def _get_room_display_name(self):
        return self.room.display_name


class AdminChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer для адміністратора.
    Адмін підключається до конкретної кімнати чату.
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated or not user.is_staff:
            await self.close()
            return

        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Позначаємо повідомлення як прочитані
        await self._mark_messages_read()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Приєднуємося до загальної групи адмінів
        await self.channel_layer.group_add(
            'admin_chat_updates',
            self.channel_name
        )

        await self.accept()

        # Надсилаємо історію
        messages = await self._get_messages()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.channel_layer.group_discard(
                'admin_chat_updates',
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get('message', '').strip()

        if not message_text:
            return

        msg = await self._save_message(message_text, 'admin')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender_type': 'admin',
                'timestamp': msg.created_at.strftime('%H:%M'),
                'message_id': msg.pk,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_type': event['sender_type'],
            'timestamp': event['timestamp'],
        }))

    async def new_message_notification(self, event):
        """Пересилаємо сповіщення адміну."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'room_id': event['room_id'],
            'room_name': event['room_name'],
            'message': event['message'],
            'sender_type': event['sender_type'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def _get_messages(self):
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
        except ChatRoom.DoesNotExist:
            return []

        msgs = room.messages.order_by('-created_at')[:100]
        return [
            {
                'message': m.text,
                'sender_type': m.sender_type,
                'timestamp': m.created_at.strftime('%H:%M'),
            }
            for m in reversed(msgs)
        ]

    @database_sync_to_async
    def _save_message(self, text, sender_type):
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
        except ChatRoom.DoesNotExist:
            return None
        return ChatMessage.objects.create(
            room=room,
            sender_type=sender_type,
            text=text
        )

    @database_sync_to_async
    def _mark_messages_read(self):
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
            room.messages.filter(sender_type='customer', is_read=False).update(is_read=True)
        except ChatRoom.DoesNotExist:
            pass
