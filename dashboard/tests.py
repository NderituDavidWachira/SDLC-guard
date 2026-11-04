import base64

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', '--password', 'Str0ng!pass', verbosity=0)

    def setUp(self):
        self.client.login(username='analyst1', password='Str0ng!pass')

    def test_dashboard_renders_five_pillars_and_png_charts(self):
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['summaries']), 5)
        png = base64.b64decode(r.context['chart_pillar'])
        self.assertTrue(png.startswith(b'\x89PNG'))

    def test_every_pillar_page_loads(self):
        for slug in ('endpoint-ide', 'vcs', 'ci-cd', 'registry', 'production'):
            r = self.client.get(reverse('pillar-detail', args=[slug]))
            self.assertEqual(r.status_code, 200)

    def test_unknown_pillar_is_404(self):
        self.assertEqual(self.client.get(reverse('pillar-detail', args=['nope'])).status_code, 404)

    def test_audit_log_restricted_by_role(self):
        self.assertEqual(self.client.get(reverse('audit-log')).status_code, 403)
        self.client.logout()
        self.client.login(username='auditor1', password='Str0ng!pass')
        self.assertEqual(self.client.get(reverse('audit-log')).status_code, 200)

    def test_filter_ignores_unknown_values(self):
        r = self.client.get(reverse('finding-list'), {'severity': "' OR 1=1 --", 'pillar': 'x'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 4)
