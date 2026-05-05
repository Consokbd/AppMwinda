from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('directeur', 'Directeur'),
        ('agent', 'Agent'),
    )

    DIRECTION_CHOICES = (
        ('design', 'Design'),
        ('marketing', 'Marketing'),
        ('finance', 'Finance'),
        ('technique', 'Technique'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    direction = models.CharField(max_length=50, choices=DIRECTION_CHOICES)

    # Fix reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )