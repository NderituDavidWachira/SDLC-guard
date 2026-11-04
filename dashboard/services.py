"""Queries that feed the dashboard and pillar pages."""
from django.db.models import Count
from django.db.models.functions import TruncWeek
from datetime import timedelta

from django.utils import timezone

from catalogue.models import Pillar
from findings.models import Finding
from findings.services import OPEN_STATUSES, SEVERITY_WEIGHTS, risk_level, risk_score

SEVERITIES = list(SEVERITY_WEIGHTS)  # Critical, High, Medium, Low


def pillar_summaries(pillars=None):
    """Per-pillar open counts by severity plus risk score and level."""
    pillars = list(pillars if pillars is not None else Pillar.objects.all())
    rows = (Finding.objects.filter(status__in=OPEN_STATUSES)
            .values('technique__pillar_id', 'severity').annotate(n=Count('id')))
    data = {p.pk: dict.fromkeys(SEVERITIES, 0) for p in pillars}
    for r in rows:
        if r['technique__pillar_id'] in data:
            data[r['technique__pillar_id']][r['severity']] = r['n']
    out = []
    for p in pillars:
        counts = data[p.pk]
        score = risk_score([s for s, n in counts.items() for _ in range(n)])
        out.append({'pillar': p, 'counts': counts, 'open': sum(counts.values()),
                    'score': score, 'level': risk_level(score)})
    return out


def severity_totals(qs):
    totals = dict.fromkeys(SEVERITIES, 0)
    for r in qs.values('severity').annotate(n=Count('id')):
        totals[r['severity']] = r['n']
    return totals


def weekly_counts(qs, weeks=8):
    since = timezone.now() - timedelta(weeks=weeks)
    rows = (qs.filter(detected_at__gte=since).annotate(week=TruncWeek('detected_at'))
            .values('week').annotate(n=Count('id')).order_by('week'))
    return [r['week'].strftime('%d %b') for r in rows], [r['n'] for r in rows]


def technique_counts(qs, limit=6):
    rows = (qs.values('technique__name').annotate(n=Count('id')).order_by('-n')[:limit])
    return [r['technique__name'] for r in rows], [r['n'] for r in rows]
