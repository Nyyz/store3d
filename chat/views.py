from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from .models import ChatRoom


@staff_member_required
def admin_chat_list(request):
    """Список всіх чат-кімнат для адміністратора."""
    rooms = ChatRoom.objects.filter(is_active=True).order_by('-created_at')
    
    rooms_data = []
    for room in rooms:
        last_msg = room.last_message
        rooms_data.append({
            'room': room,
            'last_message': last_msg,
            'unread_count': room.unread_count,
        })
    
    # Якщо є room_id в параметрах — виділяємо активну кімнату
    active_room_id = request.GET.get('room')
    
    return render(request, 'shop/admin_chat.html', {
        'rooms_data': rooms_data,
        'active_room_id': int(active_room_id) if active_room_id else None,
    })


@staff_member_required
def admin_chat_rooms_api(request):
    """API для оновлення списку кімнат (AJAX)."""
    rooms = ChatRoom.objects.filter(is_active=True).order_by('-created_at')
    data = []
    for room in rooms:
        last_msg = room.last_message
        data.append({
            'id': room.pk,
            'name': room.display_name,
            'unread_count': room.unread_count,
            'last_message': last_msg.text[:60] if last_msg else '',
            'last_time': last_msg.created_at.strftime('%H:%M') if last_msg else '',
        })
    return JsonResponse({'rooms': data})
