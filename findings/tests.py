from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalogue.models import Pillar, Technique
from findings.models import Finding

from .services import classify_severity, risk_level, risk_score


class SeverityTests(TestCase):  # TC-U01 (risk calculation)
    def test_boundaries(self):
        self.assertEqual(classify_severity(9.0), 'Critical')
        self.assertEqual(classify_severity(7.0), 'High')
        self.assertEqual(classify_severity(4.0), 'Medium')
        self.assertEqual(classify_severity(0.1), 'Low')

    def test_invalid_score(self):
        with self.assertRaises(ValueError):
            classify_severity(11)
        with self.assertRaises(ValueError):
            classify_severity(-1)

    def test_pillar_risk_score_and_level(self):
        self.assertEqual(risk_score(['Critical', 'High', 'Low']), 18)
        self.assertEqual(risk_score(['Critical'] * 12), 100)  # capped
        self.assertEqual(risk_level(19), 'Low')
        self.assertEqual(risk_level(20), 'Medium')
        self.assertEqual(risk_level(30), 'High')
        self.assertEqual(risk_level(45), 'Critical')

    def test_unknown_severity_rejected(self):
        with self.assertRaises(ValueError):
            risk_score(['Severe'])


class AccessControlTests(TestCase):  # TC-U02 (authentication / RBAC)
    def setUp(self):
        user = get_user_model()
        user.objects.create_user('aud', password='Str0ng!pass', role='auditor')
        user.objects.create_user('ana', password='Str0ng!pass', role='analyst')
        pillar = Pillar.objects.create(slug='vcs', name='VCS', order=1)
        self.technique = Technique.objects.create(sitf_id='T-1', name='Imposter Commits',
                                                  pillar=pillar)

    def test_anonymous_redirected(self):
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_auditor_cannot_raise_finding(self):
        self.client.login(username='aud', password='Str0ng!pass')
        r = self.client.post(reverse('finding-create'), {'title': 'x', 'severity': 'High'})
        self.assertEqual(r.status_code, 403)

    def test_analyst_can_raise_finding_and_severity_is_derived(self):
        self.client.login(username='ana', password='Str0ng!pass')
        r = self.client.post(reverse('finding-create'), {
            'title': 'Forged commit', 'technique': self.technique.pk, 'score': 9.5,
            'status': 'open'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Finding.objects.get().severity, 'Critical')

    def test_csv_export_neutralises_formulas(self):
        Finding.objects.create(title='=HYPERLINK("http://evil")', technique=self.technique,
                               score=5)
        self.client.login(username='aud', password='Str0ng!pass')
        body = self.client.get(reverse('findings-export')).content.decode()
        self.assertIn("'=HYPERLINK", body)
