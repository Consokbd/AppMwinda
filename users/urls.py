from django.urls import path

from .views import users_directory

urlpatterns = [
    path('', users_directory, name='users_list'),
]
