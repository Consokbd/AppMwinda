from django.db import models
from django.conf import settings

# Create your models here.

class Project(models.Model):

    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('progress', 'En cours'),
        ('done', 'Terminé'),
    )

    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='managed_projects'
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='projects'
    )

    def __str__(self):
        return self.name


class AgentTimeEntry(models.Model):
    ENTRY_TYPE_CHOICES = (
        ('work', 'Travail'),
        ('pause', 'Pause'),
        ('task', 'Tache'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    task_label = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-started_at',)

    def __str__(self):
        suffix = f" - {self.task_label}" if self.task_label else ""
        return f"{self.user.username} | {self.entry_type}{suffix}"