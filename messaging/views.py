from django.shortcuts import render, redirect
from .models import Message
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import Http404, JsonResponse
from django.db.models import Q

User = get_user_model()

# Create your views here.


@login_required
def messaging_view(request):

    users = User.objects.exclude(id=request.user.id)
    messages = Message.objects.filter(receiver=request.user).order_by('-created_at')[:50]

    if request.method == "POST":
        receiver_id = request.POST.get("receiver")
        content = request.POST.get("content")

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return render(request, 'messaging.html', {
                'users': users,
                'messages': messages,
                'error': 'Utilisateur destinataire introuvable',
                'is_management': request.user.is_superuser or request.user.role in ['admin', 'directeur'],
            })

        if not content.strip():
            return render(request, 'messaging.html', {
                'users': users,
                'messages': messages,
                'error': 'Le message ne peut pas être vide',
                'is_management': request.user.is_superuser or request.user.role in ['admin', 'directeur'],
            })

        Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content
        )

        return redirect('messaging')

    return render(request, 'messaging.html', {
        'users': users,
        'messages': messages,
        'is_management': request.user.is_superuser or request.user.role in ['admin', 'directeur'],
    })


@login_required
def get_messages(request, user_id):
    """API pour récupérer les messages d'une conversation"""
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    # Récupérer tous les messages de la conversation (envoyés et reçus)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')
    
    # Marquer tous les messages reçus comme lus
    Message.objects.filter(
        sender=other_user, 
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'content': msg.content,
            'created_at': msg.created_at.strftime("%H:%M"),
            'is_sent': msg.sender.id == request.user.id,
            'is_read': msg.is_read
        })
    
    return JsonResponse({'messages': messages_data})


@login_required
def get_unread_count(request):
    """API pour récupérer le nombre de messages non lus"""
    unread_count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    # Récupérer aussi les conversations avec messages non lus
    unread_conversations = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).values('sender').distinct().count()
    
    return JsonResponse({
        'unread_count': unread_count,
        'unread_conversations': unread_conversations
    })


@login_required
def get_conversations(request):
    """API pour récupérer tous les contacts avec leurs messages non lus"""
    users = User.objects.exclude(id=request.user.id)
    
    conversations = []
    for user in users:
        unread_count = Message.objects.filter(
            sender=user,
            receiver=request.user,
            is_read=False
        ).count()
        
        conversations.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'unread_count': unread_count
        })
    
    return JsonResponse({'conversations': conversations})