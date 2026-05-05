from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import DailyReport

User = get_user_model()


class ReportsFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reporter',
            password='testpass123',
            email='reporter@example.com',
            role='agent',
            direction='marketing',
        )

    def test_authenticated_user_can_create_daily_report(self):
        self.client.login(username='reporter', password='testpass123')
        response = self.client.post(
            reverse('reports_list'),
            {
                'date': '2026-04-08',
                'project': 'Projet Test',
                'work_done': 'Tâches terminées',
                'problems': 'Aucun',
                'objectives': 'Continuer le sprint',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DailyReport.objects.count(), 1)
        self.assertEqual(DailyReport.objects.first().user, self.user)
