from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import DailyReport

User = get_user_model()


@login_required(login_url='login')
def reports_list(request):
    reports = DailyReport.objects.select_related('user').order_by('-date', '-created_at')
    is_management = request.user.is_superuser or request.user.role in ['admin', 'directeur']

    if not is_management:
        reports = reports.filter(user=request.user)
    else:
        selected_user = request.GET.get('user_id', '').strip()
        if selected_user:
            reports = reports.filter(user_id=selected_user)

    if request.method == 'POST':
        if is_management:
            messages.error(request, "La direction consulte les rapports, les agents les soumettent.")
            return redirect('reports_list')

        # Récupérer les nouveaux champs
        department = request.POST.get('department', '').strip()
        project = request.POST.get('project', '').strip()
        team_agent = request.POST.get('team_agent', '').strip()
        observations = request.POST.get('observations', '').strip()

        # Checkboxes pour conception
        conception_brief_received = 'conception_brief_received' in request.POST
        conception_croquis_validated = 'conception_croquis_validated' in request.POST
        conception_modeling_done = 'conception_modeling_done' in request.POST
        conception_file_ready = 'conception_file_ready' in request.POST

        # Checkboxes pour découpe
        decoupe_bois_decoupe = 'decoupe_bois_decoupe' in request.POST
        decoupe_metal_decoupe = 'decoupe_metal_decoupe' in request.POST
        decoupe_pvc_decoupe = 'decoupe_pvc_decoupe' in request.POST
        decoupe_dimensions_verified = 'decoupe_dimensions_verified' in request.POST

        # Assemblage
        assemblage_method = request.POST.get('assemblage_method', '').strip()
        assemblage_partial = 'assemblage_partial' in request.POST
        assemblage_complete = 'assemblage_complete' in request.POST
        assemblage_renforts = 'assemblage_renforts' in request.POST

        # Installation LED
        led_bande_posee = 'led_bande_posee' in request.POST
        led_alimentation_installee = 'led_alimentation_installee' in request.POST
        led_test_allumage = 'led_test_allumage' in request.POST
        led_cablage_secure = 'led_cablage_secure' in request.POST

        # Contrôle qualité
        qualite_alignement = 'qualite_alignement' in request.POST
        qualite_solidite = 'qualite_solidite' in request.POST
        qualite_finitions = 'qualite_finitions' in request.POST
        qualite_conformite = 'qualite_conformite' in request.POST
        qualite_validation = 'qualite_validation' in request.POST

        # Peinture & finition
        peinture_poncage = 'peinture_poncage' in request.POST
        peinture_sous_couche = 'peinture_sous_couche' in request.POST
        peinture_peinture = 'peinture_peinture' in request.POST
        peinture_vernis = 'peinture_vernis' in request.POST
        peinture_nettoyage = 'peinture_nettoyage' in request.POST

        # Livraison
        livraison_emballage = 'livraison_emballage' in request.POST
        livraison_transport = 'livraison_transport' in request.POST
        livraison_installation = 'livraison_installation' in request.POST
        livraison_rapport_photo = 'livraison_rapport_photo' in request.POST
        livraison_projet_cloture = 'livraison_projet_cloture' in request.POST

        # Anciens champs (optionnels maintenant)
        work_done = request.POST.get('work_done', '').strip()
        problems = request.POST.get('problems', '').strip()
        objectives = request.POST.get('objectives', '').strip()
        report_date = request.POST.get('date', '').strip() or str(timezone.localdate())

        # Validation basique
        if not project:
            messages.error(request, "Le champ 'Projet' est obligatoire.")
            return redirect('reports_list')

        DailyReport.objects.create(
            user=request.user,
            date=report_date,
            department=department,
            project=project,
            team_agent=team_agent,
            conception_brief_received=conception_brief_received,
            conception_croquis_validated=conception_croquis_validated,
            conception_modeling_done=conception_modeling_done,
            conception_file_ready=conception_file_ready,
            decoupe_bois_decoupe=decoupe_bois_decoupe,
            decoupe_metal_decoupe=decoupe_metal_decoupe,
            decoupe_pvc_decoupe=decoupe_pvc_decoupe,
            decoupe_dimensions_verified=decoupe_dimensions_verified,
            assemblage_method=assemblage_method,
            assemblage_partial=assemblage_partial,
            assemblage_complete=assemblage_complete,
            assemblage_renforts=assemblage_renforts,
            led_bande_posee=led_bande_posee,
            led_alimentation_installee=led_alimentation_installee,
            led_test_allumage=led_test_allumage,
            led_cablage_secure=led_cablage_secure,
            qualite_alignement=qualite_alignement,
            qualite_solidite=qualite_solidite,
            qualite_finitions=qualite_finitions,
            qualite_conformite=qualite_conformite,
            qualite_validation=qualite_validation,
            peinture_poncage=peinture_poncage,
            peinture_sous_couche=peinture_sous_couche,
            peinture_peinture=peinture_peinture,
            peinture_vernis=peinture_vernis,
            peinture_nettoyage=peinture_nettoyage,
            livraison_emballage=livraison_emballage,
            livraison_transport=livraison_transport,
            livraison_installation=livraison_installation,
            livraison_rapport_photo=livraison_rapport_photo,
            livraison_projet_cloture=livraison_projet_cloture,
            observations=observations,
            work_done=work_done,
            problems=problems,
            objectives=objectives,
        )
        messages.success(request, "Rapport enregistré avec succès.")
        return redirect('reports_list')

    context = {
        'reports': reports,
        'default_date': timezone.localdate(),
        'is_admin': request.user.is_superuser or request.user.role == 'admin',
        'is_management': is_management,
        'agents': User.objects.filter(role='agent').order_by('username') if is_management else [],
        'selected_user': request.GET.get('user_id', '').strip() if is_management else '',
        'can_create_report': not is_management,
    }
    return render(request, 'reports.html', context)
