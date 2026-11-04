# SDLC Guard

A Django security dashboard for the SDLC "code factory" (SITF pillars: Endpoint/IDE, VCS,
CI/CD, Registry, Production). BCS 3106 Software Engineering semester project.

## Quick start (Windows PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DJANGO_DEBUG = "1"
python manage.py migrate
python manage.py seed_demo --password "Demo#Pass2026x"
python manage.py runserver
```

Linux/macOS: use `source venv/bin/activate` and `export DJANGO_DEBUG=1`.

Open http://127.0.0.1:8000 and sign in with one of the demo users
(`admin1`, `analyst1`, `devops1`, `auditor1`) and the password you passed to `seed_demo`.
Create a real admin with `python manage.py createsuperuser`.

## Roles (RBAC)

| Role | Can do |
|---|---|
| Admin | Everything, audit log, Django admin site |
| Analyst | Raise/edit findings, assign tasks, export CSV |
| DevOps | View findings, update remediation task status |
| Auditor | Read-only, export CSV, view audit log |

## Commands

```bash
python manage.py test                       # unit tests (17)
coverage run manage.py test && coverage report
flake8 .                                    # lint
bandit -r accounts audit catalogue config dashboard findings sources -x '*/tests.py' -q
pip-audit -r requirements.txt               # vulnerable dependencies
```

## Layout

`accounts` users/roles/login throttling, `catalogue` pillars + techniques,
`sources` data sources, `findings` findings/tasks/risk rules, `dashboard` charts + pages,
`audit` audit log. CI/CD: `.circleci/config.yml`, `Dockerfile`, `scripts/deploy_staging.sh`.

## Production notes

Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`. Cookies, HSTS and HTTPS
redirect turn on automatically when DEBUG is off. Demo technique IDs are illustrative; replace
them with entries from the official SITF catalogue.

## Not implemented yet

MFA (the `mfa_enabled` field exists; add `django-otp` to enforce it), AlertRule and Report
models (CSV export covers reporting), live GitHub API connector (data is loaded by seed or admin).
