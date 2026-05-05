from django.urls import path
from .views import messaging_view, get_messages, get_unread_count, get_conversations

urlpatterns = [
    path('', messaging_view, name='messaging'),
    path('api/messages/<int:user_id>/', get_messages, name='get_messages'),
    path('api/unread-count/', get_unread_count, name='get_unread_count'),
    path('api/conversations/', get_conversations, name='get_conversations'),
]