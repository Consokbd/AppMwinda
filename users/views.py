from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from projects.models import AgentTimeEntry

User = get_user_model()


def _format_seconds(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            try:
                has_open_work = AgentTimeEntry.objects.filter(
                    user=user,
                    entry_type='work',
                    ended_at__isnull=True,
                ).exists()
                if not has_open_work:
                    AgentTimeEntry.objects.create(
                        user=user,
                        entry_type='work',
                        started_at=timezone.now(),
                    )
            except Exception:
                # Silently continue if AgentTimeEntry creation fails (e.g., migrations not run)
                pass
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Identifiants invalides'})
    
    return render(request, 'login.html')


def logout_view(request):
    if request.user.is_authenticated:
        now = timezone.now()
        open_entries = AgentTimeEntry.objects.filter(
            user=request.user,
            entry_type__in=['work', 'pause', 'task'],
            ended_at__isnull=True,
        )
        for entry in open_entries:
            elapsed = int((now - entry.started_at).total_seconds())
            entry.duration_seconds = entry.duration_seconds + max(elapsed, 0)
            entry.ended_at = now
            entry.save(update_fields=['duration_seconds', 'ended_at'])

    logout(request)
    return redirect('login')


@login_required(login_url='login')
def users_directory(request):
    is_management = request.user.is_superuser or request.user.role in ['admin', 'directeur']
    users = User.objects.filter(role='agent').order_by('username') if is_management else User.objects.all().order_by('username')

    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    direction = request.GET.get('direction', '').strip()

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if role:
        users = users.filter(role=role)

    if direction:
        users = users.filter(direction=direction)

    now = timezone.now()
    for user in users:
        entries = AgentTimeEntry.objects.filter(user=user)

        task_entries = entries.filter(entry_type='task', ended_at__isnull=False)
        task_durations = [entry.duration_seconds for entry in task_entries]
        avg_task_seconds = int(sum(task_durations) / len(task_durations)) if task_durations else 0
        total_task_seconds = sum(task_durations)

        work_entries = entries.filter(entry_type='work')
        work_seconds = sum(
            (entry.duration_seconds + max(int((now - entry.started_at).total_seconds()), 0))
            if entry.ended_at is None else entry.duration_seconds
            for entry in work_entries
        )
        pause_entries = entries.filter(entry_type='pause')
        pause_seconds = sum(
            (entry.duration_seconds + max(int((now - entry.started_at).total_seconds()), 0))
            if entry.ended_at is None else entry.duration_seconds
            for entry in pause_entries
        )

        performance = int(min(100, round((total_task_seconds / work_seconds) * 100))) if work_seconds else 0

        user.performance_score = performance
        user.avg_task_time = _format_seconds(avg_task_seconds)
        user.work_time_total = _format_seconds(work_seconds)
        user.pause_time_total = _format_seconds(pause_seconds)

    full_name = request.user.get_full_name() or request.user.username
    profile_progress = 75
    current_project = {
        'title': 'Conception logo 3D',
        'description': 'Aperçu sur la description du projet en cours',
        'button_text': 'OUVRIR',
    }
    tasks = [
        {'label': 'Conception du logo', 'active': True},
        {'label': 'Préparation du fichier de découpe', 'active': False},
        {'label': 'Relecture du brief', 'active': False},
    ]
    time_stats = [
        {'label': 'T. sur une tâche', 'value': '00:01:54', 'highlight': True},
        {'label': 'Temps de travail', 'value': '04:01:54'},
        {'label': 'Temps de pause', 'value': '00:00:00'},
    ]

    context = {
        'users': users,
        'query': query,
        'selected_role': role,
        'selected_direction': direction,
        'role_choices': User.ROLE_CHOICES,
        'direction_choices': User.DIRECTION_CHOICES,
        'full_name': full_name,
        'profile_progress': profile_progress,
        'current_project': current_project,
        'tasks': tasks,
        'time_stats': time_stats,
        'is_admin': request.user.is_superuser or request.user.role == 'admin',
        'is_management': is_management,
    }
    return render(request, 'users.html', context)
