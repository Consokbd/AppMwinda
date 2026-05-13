from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Q
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Project
from .models import AgentTimeEntry, ProjectAssignmentNotification
from reports.models import DailyReport
from messaging.models import Message
from django.contrib.auth import get_user_model

User = get_user_model()


def _format_seconds(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _entry_elapsed_seconds(entry, now):
    elapsed = int((now - entry.started_at).total_seconds())
    return entry.duration_seconds + max(elapsed, 0)


def _close_entry(entry, now):
    entry.duration_seconds = _entry_elapsed_seconds(entry, now)
    entry.ended_at = now
    entry.save(update_fields=['duration_seconds', 'ended_at'])


def _open_entry_for_user(user, entry_type):
    return AgentTimeEntry.objects.filter(
        user=user,
        entry_type=entry_type,
        ended_at__isnull=True,
    ).first()


def _ensure_work_session(user):
    try:
        if _open_entry_for_user(user, 'work'):
            return
        AgentTimeEntry.objects.create(
            user=user,
            entry_type='work',
            started_at=timezone.now(),
        )
    except Exception:
        # Silently continue if AgentTimeEntry creation fails (e.g., migrations not run)
        pass

# Décorateur pour vérifier si l'utilisateur est admin
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser and request.user.role != 'admin':
            return HttpResponseForbidden("Vous n'avez pas l'accès administrateur")
        return view_func(request, *args, **kwargs)
    return wrapper


# Create your views here.

@login_required(login_url='login')
@ensure_csrf_cookie
def dashboard(request):
    _ensure_work_session(request.user)
    is_management = request.user.is_superuser or request.user.role in ['admin', 'directeur']

    if is_management:
        projects_qs = Project.objects.select_related('manager').prefetch_related('members')
        project_status_counts = {
            'pending': projects_qs.filter(status='pending').count(),
            'progress': projects_qs.filter(status='progress').count(),
            'done': projects_qs.filter(status='done').count(),
        }
        total_projects = sum(project_status_counts.values())
        progress_ratio = round((project_status_counts['done'] / total_projects) * 100) if total_projects else 0

        context = {
            'is_admin': request.user.is_superuser or request.user.role == 'admin',
            'is_management': True,
            'project_status_counts': project_status_counts,
            'total_projects': total_projects,
            'progress_ratio': progress_ratio,
            'recent_projects': projects_qs.order_by('-start_date')[:8],
        }
        return render(request, "management_dashboard.html", context)

    projects = Project.objects.all()
    reports = DailyReport.objects.select_related('user').order_by('-date', '-created_at')[:5]

    # Compter les messages non lus
    unread_messages_count = Message.objects.filter(receiver=request.user, is_read=False).count()

    # Compter les nouvelles assignations de projets (projets où l'utilisateur a été récemment assigné)
    new_project_assignments = Project.objects.filter(members=request.user).count()

    # Contexte utilisateur
    full_name = request.user.get_full_name() or request.user.username
    user_first_letter = (request.user.first_name or request.user.username)[0].upper()
    user_role_display = dict(request.user.ROLE_CHOICES).get(request.user.role, request.user.role)

    # Projet courant basé sur les vraies assignations
    assigned_projects = Project.objects.filter(members=request.user).order_by('-start_date')
    current_project_obj = (
        assigned_projects.filter(status='progress').first()
        or assigned_projects.first()
    )

    current_project = {
        'title': current_project_obj.name if current_project_obj else 'Aucun projet assigné',
        'description': (
            current_project_obj.description[:140]
            if current_project_obj and current_project_obj.description
            else "Aucune assignation active pour le moment."
        ),
        'button_text': 'OUVRIR',
        'status_display': current_project_obj.get_status_display() if current_project_obj else '',
    }

    now = timezone.now()
    today = timezone.localdate()
    try:
        today_entries = AgentTimeEntry.objects.filter(user=request.user, started_at__date=today)
    except Exception:
        today_entries = []

    # Toujours démarrer avec des tâches non cochées lors d'une nouvelle connexion.
    task_definitions = [
        'Réception du brief',
        'Analyse des besoins',
        'Croquis initial',
        'Validation du croquis',
        'Modélisation 2D/3D',
        'Préparation du fichier final',
        'Contrôle qualité',
        'Corrections finales',
        'Validation client',
        'Clôture de la tâche',
    ]
    profile_progress = 0
    tasks = [
        {'label': label, 'active': False, 'visible': index < 3}
        for index, label in enumerate(task_definitions)
    ]

    total_work_seconds = sum(
        _entry_elapsed_seconds(entry, now) if entry.ended_at is None else entry.duration_seconds
        for entry in today_entries.filter(entry_type='work')
    )
    total_pause_seconds = sum(
        _entry_elapsed_seconds(entry, now) if entry.ended_at is None else entry.duration_seconds
        for entry in today_entries.filter(entry_type='pause')
    )

    active_task_entry = _open_entry_for_user(request.user, 'task')
    task_elapsed_seconds = _entry_elapsed_seconds(active_task_entry, now) if active_task_entry else 0

    # Stats basées sur les minuteurs réels
    time_stats = [
        {'label': 'T. sur une tâche', 'value': _format_seconds(task_elapsed_seconds), 'highlight': True},
        {'label': 'Temps de travail', 'value': _format_seconds(total_work_seconds)},
        {'label': 'Temps de pause', 'value': _format_seconds(total_pause_seconds)},
    ]

    # Vérifier si l'utilisateur est admin pour afficher le bouton Users
    is_admin = request.user.is_superuser or request.user.role == 'admin'

    open_pause_entry = _open_entry_for_user(request.user, 'pause')
    open_work_entry = _open_entry_for_user(request.user, 'work')

    context = {
        "projects": projects,
        "reports": reports,
        "full_name": full_name,
        "user_first_letter": user_first_letter,
        "user_role_display": user_role_display,
        "profile_progress": profile_progress,
        "current_project": current_project,
        "tasks": tasks,
        "time_stats": time_stats,
        "is_admin": is_admin,
        "unread_messages_count": unread_messages_count,
        "new_project_assignments": new_project_assignments,
        "timer_state": {
            "active_task_label": active_task_entry.task_label if active_task_entry else "",
            "active_task_started_at": active_task_entry.started_at.isoformat() if active_task_entry else "",
            "active_pause_started_at": open_pause_entry.started_at.isoformat() if open_pause_entry else "",
            "active_work_started_at": open_work_entry.started_at.isoformat() if open_work_entry else "",
            "is_pause_running": open_pause_entry is not None,
            "is_work_running": open_work_entry is not None,
        },
        "task_labels": task_definitions,
    }

    return render(request, "dashboard.html", context)


@login_required(login_url='login')
@require_POST
def start_task_timer(request):
    task_label = request.POST.get('task_label', '').strip()
    if not task_label:
        return JsonResponse({'error': 'task_label requis'}, status=400)

    now = timezone.now()
    open_pause = _open_entry_for_user(request.user, 'pause')
    if open_pause:
        _close_entry(open_pause, now)

    open_task = _open_entry_for_user(request.user, 'task')
    if open_task and open_task.task_label != task_label:
        _close_entry(open_task, now)

    if not _open_entry_for_user(request.user, 'task'):
        AgentTimeEntry.objects.create(
            user=request.user,
            entry_type='task',
            task_label=task_label,
            started_at=now,
        )

    return JsonResponse({'ok': True, 'task_label': task_label})


@login_required(login_url='login')
@require_POST
def complete_task_timer(request):
    task_label = request.POST.get('task_label', '').strip()
    now = timezone.now()

    open_task = _open_entry_for_user(request.user, 'task')
    if not open_task:
        return JsonResponse({'ok': True, 'duration_seconds': 0})

    if task_label and open_task.task_label != task_label:
        return JsonResponse({'error': 'Cette tâche n’est pas active'}, status=409)

    _close_entry(open_task, now)
    return JsonResponse({'ok': True, 'duration_seconds': open_task.duration_seconds})


@login_required(login_url='login')
@require_POST
def toggle_pause_timer(request):
    now = timezone.now()
    open_pause = _open_entry_for_user(request.user, 'pause')

    if open_pause:
        _close_entry(open_pause, now)
        return JsonResponse({'ok': True, 'is_pause_running': False, 'duration_seconds': open_pause.duration_seconds})

    AgentTimeEntry.objects.create(
        user=request.user,
        entry_type='pause',
        started_at=now,
    )
    return JsonResponse({'ok': True, 'is_pause_running': True})


@login_required(login_url='login')
def projects_list(request):
    projects = Project.objects.select_related('manager').prefetch_related('members').order_by('-start_date')

    status = request.GET.get('status', '').strip()
    if status:
        projects = projects.filter(status=status)

    is_manager = request.user.role in ['admin', 'directeur'] or request.user.is_superuser

    if request.method == 'POST':
        if not is_manager:
            return HttpResponseForbidden("Vous n'avez pas la permission de créer un projet.")

        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        project_status = request.POST.get('status', 'pending').strip() or 'pending'
        member_ids = request.POST.getlist('members')

        if not all([name, description, start_date, end_date]):
            messages.error(request, "Tous les champs du projet sont requis.")
            return redirect('projects_list')

        project = Project.objects.create(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=project_status,
            manager=request.user,
        )

        if member_ids:
            members = User.objects.filter(id__in=member_ids)
            project.members.set(members)
            for member in members:
                if member.id != request.user.id:
                    ProjectAssignmentNotification.objects.get_or_create(
                        user=member,
                        project=project,
                    )

        messages.success(request, "Projet créé avec succès.")
        return redirect('projects_list')

    ProjectAssignmentNotification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(is_read=True)

    context = {
        'projects': projects,
        'status_choices': Project.STATUS_CHOICES,
        'selected_status': status,
        'can_create_project': is_manager,
        'available_users': User.objects.all().order_by('username'),
        'is_admin': request.user.is_superuser or request.user.role == 'admin',
        'is_management': request.user.is_superuser or request.user.role in ['admin', 'directeur'],
    }
    return render(request, 'projects.html', context)


@login_required(login_url='login')
def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related('manager').prefetch_related('members'),
        id=project_id,
    )

    is_manager_role = request.user.role in ['admin', 'directeur'] or request.user.is_superuser
    is_member = project.members.filter(id=request.user.id).exists()
    is_owner = project.manager_id == request.user.id

    if not (is_manager_role or is_member or is_owner):
        return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à ce projet.")

    context = {
        'project': project,
        'is_admin': request.user.is_superuser or request.user.role == 'admin',
        'is_management': request.user.is_superuser or request.user.role in ['admin', 'directeur'],
    }
    return render(request, 'project_detail.html', context)


# ===== VUES ADMIN =====

@admin_required
def admin_dashboard(request):
    """Dashboard d'admin avec statistiques"""
    
    users_count = User.objects.count()
    projects_count = Project.objects.count()
    messages_count = Message.objects.count()
    reports_count = DailyReport.objects.count()
    
    # Statistiques par statut de projet
    projects_by_status = Project.objects.values('status').annotate(count=Count('id'))
    
    # Derniers messages
    recent_messages = Message.objects.select_related('sender', 'receiver').order_by('-created_at')[:10]
    
    # Derniers rapports
    recent_reports = DailyReport.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'users_count': users_count,
        'projects_count': projects_count,
        'messages_count': messages_count,
        'reports_count': reports_count,
        'projects_by_status': projects_by_status,
        'recent_messages': recent_messages,
        'recent_reports': recent_reports,
    }
    
    return render(request, 'admin/dashboard.html', context)


@admin_required
def admin_users(request):
    """Gestion des utilisateurs"""
    
    users = User.objects.all().order_by('-date_joined')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            
            if action == 'delete':
                user.delete()
            elif action == 'make_admin':
                user.is_superuser = True
                user.is_staff = True
                user.role = 'admin'
                user.save()
            elif action == 'remove_admin':
                user.is_superuser = False
                user.is_staff = False
                user.role = 'agent'
                user.save()
        except User.DoesNotExist:
            pass
        
        return redirect('admin_users')
    
    context = {
        'users': users,
    }
    
    return render(request, 'admin/users.html', context)


@admin_required
def admin_create_user(request):
    """Créer un nouvel utilisateur"""
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role', 'agent')
        direction = request.POST.get('direction', 'design')
        is_admin = request.POST.get('is_admin') == 'on'
        
        errors = []
        
        # Validation
        if not username:
            errors.append('Le nom d\'utilisateur est requis')
        elif User.objects.filter(username=username).exists():
            errors.append('Ce nom d\'utilisateur existe déjà')
        
        if not email:
            errors.append('L\'email est requis')
        elif User.objects.filter(email=email).exists():
            errors.append('Cet email existe déjà')
        
        if not password:
            errors.append('Le mot de passe est requis')
        elif len(password) < 6:
            errors.append('Le mot de passe doit contenir au moins 6 caractères')
        
        if password != password_confirm:
            errors.append('Les mots de passe ne correspondent pas')
        
        if not errors:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                direction=direction,
            )
            
            if is_admin:
                user.is_superuser = True
                user.is_staff = True
                user.save()
            
            return redirect('admin_users')
        
        context = {
            'errors': errors,
            'form_data': request.POST,
            'role_choices': User.ROLE_CHOICES,
            'direction_choices': User.DIRECTION_CHOICES,
        }
    else:
        context = {
            'role_choices': User.ROLE_CHOICES,
            'direction_choices': User.DIRECTION_CHOICES,
        }
    
    return render(request, 'admin/create_user.html', context)


@admin_required
def admin_projects(request):
    """Gestion des projets"""
    
    projects = Project.objects.select_related('manager').prefetch_related('members').order_by('-start_date')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        project_id = request.POST.get('project_id')
        
        try:
            project = Project.objects.get(id=project_id)
            
            if action == 'delete':
                project.delete()
            elif action == 'status':
                new_status = request.POST.get('status')
                project.status = new_status
                project.save()
        except Project.DoesNotExist:
            pass
        
        return redirect('admin_projects')
    
    context = {
        'projects': projects,
        'status_choices': Project.STATUS_CHOICES,
    }
    
    return render(request, 'admin/projects.html', context)


@admin_required
def admin_messages(request):
    """Vue des messages entre utilisateurs"""
    
    messages = Message.objects.select_related('sender', 'receiver').order_by('-created_at')
    
    # Filtre par utilisateur si fourni
    user_id = request.GET.get('user_id')
    if user_id:
        messages = messages.filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
    
    users = User.objects.all().order_by('username')
    
    context = {
        'messages': messages,
        'users': users,
        'selected_user': user_id,
    }
    
    return render(request, 'admin/messages.html', context)


@admin_required
def admin_reports(request):
    """Vue des rapports quotidiens"""
    
    reports = DailyReport.objects.select_related('user').order_by('-created_at')
    
    # Filtre par utilisateur si fourni
    user_id = request.GET.get('user_id')
    if user_id:
        reports = reports.filter(user_id=user_id)
    
    users = User.objects.all().order_by('username')
    
    context = {
        'reports': reports,
        'users': users,
        'selected_user': user_id,
    }
    
    return render(request, 'admin/reports.html', context)
