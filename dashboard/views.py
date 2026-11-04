from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from catalogue.models import Pillar
from findings.models import Finding
from findings.services import OPEN_STATUSES

from . import charts, services


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        summaries = services.pillar_summaries()
        open_qs = Finding.objects.filter(status__in=OPEN_STATUSES)
        totals = services.severity_totals(open_qs)
        names = [s['pillar'].name for s in summaries]
        matrix = {sev: [s['counts'][sev] for s in summaries] for sev in services.SEVERITIES}
        labels, values = services.weekly_counts(Finding.objects.all())
        tech_names, tech_counts = services.technique_counts(open_qs)
        ctx.update(
            summaries=summaries,
            totals=totals,
            open_total=sum(totals.values()),
            critical_open=totals['Critical'],
            recent=Finding.objects.select_related('technique__pillar')[:6],
            chart_pillar=charts.findings_by_pillar(names, matrix),
            chart_severity=charts.severity_donut(totals),
            chart_trend=charts.weekly_trend(labels, values),
            chart_techniques=charts.top_techniques(tech_names, tech_counts),
        )
        return ctx


class PillarDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/pillar_detail.html'

    def get_context_data(self, slug, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pillar = get_object_or_404(Pillar, slug=slug)
        summary = services.pillar_summaries([pillar])[0]
        qs = Finding.objects.filter(technique__pillar=pillar).select_related(
            'technique', 'data_source')
        open_qs = qs.filter(status__in=OPEN_STATUSES)
        t_names, t_counts = services.technique_counts(open_qs, limit=5)
        labels, values = services.weekly_counts(qs)
        ctx.update(
            pillar=pillar, summary=summary,
            findings=open_qs[:12],
            techniques=pillar.techniques.all(),
            sources=pillar.sources.all(),
            chart_severity=charts.severity_donut(services.severity_totals(open_qs)),
            chart_techniques=charts.top_techniques(t_names, t_counts),
            chart_trend=charts.weekly_trend(labels, values),
        )
        return ctx
