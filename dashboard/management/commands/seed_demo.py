"""Load SAMPLE data: pillars, illustrative techniques, sources, users, findings.

The technique names/IDs are illustrative demo data. Replace them with entries
from the official SITF catalogue (https://wiz-sec-public.github.io/SITF/).
"""
import random
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from catalogue.models import Pillar, Technique
from findings.models import Finding, RemediationTask
from sources.models import DataSource

PILLARS = [
    ('endpoint-ide', 'Endpoint/IDE', 'Developer workstations, IDEs and extensions.'),
    ('vcs', 'VCS', 'Source control: repositories, branches, commits, pull requests.'),
    ('ci-cd', 'CI/CD', 'Pipelines, build runners and workflow automation.'),
    ('registry', 'Registry', 'Package and container registries.'),
    ('production', 'Production', 'Deployed workloads and release credentials.'),
]
TECHNIQUES = {
    'endpoint-ide': ['Malicious IDE Extension', 'Compromised Developer Workstation',
                     'Credential Theft from Dev Environment', 'Poisoned Local Git Hook'],
    'vcs': ['Imposter Commits', 'Branch Protection Bypass',
            'Secrets Leaked in Repository', 'Malicious Pull Request'],
    'ci-cd': ['Action Cache Poisoning', 'Compromised Build Runner',
              'Pipeline Secret Exfiltration', 'Untrusted Workflow Injection'],
    'registry': ['Dependency Confusion', 'Typosquatted Package',
                 'Image Tag Overwrite', 'Stolen Registry Token'],
    'production': ['Unsigned Artifact Deployed', 'Over-privileged Deploy Credentials',
                   'Drift from Approved Build', 'Compromised Release Pipeline'],
}
SOURCES = [('GitHub Enterprise', 'github', 'vcs'), ('Developer EDR', 'endpoint', 'endpoint-ide'),
           ('CircleCI', 'ci', 'ci-cd'), ('Container Registry', 'registry', 'registry'),
           ('Prod Deploy Monitor', 'cloud', 'production')]
USERS = [('admin1', 'admin'), ('analyst1', 'analyst'), ('devops1', 'devops'),
         ('auditor1', 'auditor')]
ASSETS = ['payments-api', 'web-frontend', 'auth-service', 'data-pipeline', 'mobile-app',
          'build-runner-03', 'infra-modules']
SCORES = [9.6, 9.1, 8.2, 7.4, 7.0, 6.1, 5.5, 4.8, 4.0, 3.2, 2.1, 1.0]


class Command(BaseCommand):
    help = 'Create sample SDLC Guard data for demos and testing.'

    def add_arguments(self, parser):
        parser.add_argument('--password', help='Password for demo users (random if omitted)')

    def handle(self, *args, **opts):
        rng = random.Random(42)  # nosec B311
        password = opts['password'] or secrets.token_urlsafe(12)
        pillars = {}
        for order, (slug, name, desc) in enumerate(PILLARS, start=1):
            pillars[slug], _ = Pillar.objects.get_or_create(
                slug=slug, defaults={'name': name, 'description': desc, 'order': order})
        techs = []
        for slug, names in TECHNIQUES.items():
            for i, name in enumerate(names, start=1):
                t, _ = Technique.objects.get_or_create(
                    sitf_id=f"DEMO-{slug.replace('-', '')[:3].upper()}-{i:02d}",
                    defaults={'name': name, 'pillar': pillars[slug],
                              'description': f'Illustrative technique: {name}.',
                              'base_severity': rng.choice(['High', 'Medium', 'Critical'])})
                techs.append(t)
        sources = [DataSource.objects.get_or_create(
            name=n, defaults={'source_type': t, 'pillar': pillars[p],
                              'last_sync': timezone.now()})[0] for n, t, p in SOURCES]
        users = {}
        User = get_user_model()
        for username, role in USERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={'role': role, 'email': f'{username}@example.com',
                                             'is_staff': role == 'admin'})
            if created:
                user.set_password(password)
                user.save()
            users[role] = user
        if not Finding.objects.exists():
            now = timezone.now()
            for n in range(1, 46):
                tech = rng.choice(techs)
                f = Finding.objects.create(
                    title=f'{tech.name} detected on {rng.choice(ASSETS)}',
                    description=f'Sample incident related to {tech.name}.',
                    technique=tech,
                    data_source=next(x for x in sources if x.pillar_id == tech.pillar_id),
                    score=rng.choice(SCORES),
                    status=rng.choices(['open', 'investigating', 'resolved', 'false_positive'],
                                       weights=[50, 20, 25, 5])[0],
                    detected_at=now - timedelta(days=rng.randint(0, 55), hours=rng.randint(0, 23)),
                    incident_ref=f'INC-{n:04d}', affected_asset=rng.choice(ASSETS),
                    reported_by=users['analyst'])
                if f.is_open and rng.random() < 0.4:
                    RemediationTask.objects.create(
                        finding=f, assignee=users['devops'],
                        due_date=(now + timedelta(days=rng.randint(2, 14))).date(),
                        notes='Rotate credentials and review access.')
        self.stdout.write(self.style.SUCCESS('Sample data loaded.'))
        if not opts['password']:
            self.stdout.write('Demo users: admin1, analyst1, devops1, auditor1')
            self.stdout.write(f'Password: {password}')
