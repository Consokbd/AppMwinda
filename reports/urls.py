from django.urls import path

from .views import reports_list

urlpatterns = [
    path('', reports_list, name='reports_list'),
]
