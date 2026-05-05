from django.urls import path

from .views import projects_list, project_detail, start_task_timer, complete_task_timer, toggle_pause_timer

urlpatterns = [
    path('', projects_list, name='projects_list'),
    path('<int:project_id>/', project_detail, name='project_detail'),
    path('api/timer/start-task/', start_task_timer, name='start_task_timer'),
    path('api/timer/complete-task/', complete_task_timer, name='complete_task_timer'),
    path('api/timer/toggle-pause/', toggle_pause_timer, name='toggle_pause_timer'),
]
