def app_notifications(request):
    if not request.user.is_authenticated:
        return {
            'unread_messages_count': 0,
            'unread_project_assignments': 0,
        }

    from messaging.models import Message
    from projects.models import ProjectAssignmentNotification
    from django.db import OperationalError, ProgrammingError

    try:
        unread_messages_count = Message.objects.filter(
            receiver=request.user,
            is_read=False,
        ).count()
        unread_project_assignments = ProjectAssignmentNotification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()
    except (OperationalError, ProgrammingError):
        unread_messages_count = 0
        unread_project_assignments = 0

    return {
        'unread_messages_count': unread_messages_count,
        'unread_project_assignments': unread_project_assignments,
    }
