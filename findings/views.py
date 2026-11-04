import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from audit.utils import record
from catalogue.models import Pillar, Severity

from .forms import FindingForm, TaskForm
from .models import Finding, RemediationTask

WRITE_ROLES = ('admin', 'analyst')


def filtered_findings(params):
    """Apply GET filters using whitelists only (no raw user input in queries)."""
    qs = Finding.objects.select_related('technique__pillar', 'data_source')
    pillar = params.get('pillar', '')
    if pillar in Pillar.objects.values_list('slug', flat=True):
        qs = qs.filter(technique__pillar__slug=pillar)
    if params.get('severity') in Severity.values:
        qs = qs.filter(severity=params['severity'])
    if params.get('status') in Finding.Status.values:
        qs = qs.filter(status=params['status'])
    return qs


class FindingListView(LoginRequiredMixin, ListView):
    paginate_by = 20
    template_name = 'findings/finding_list.html'

    def get_queryset(self):
        return filtered_findings(self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop('page', None)
        ctx.update(pillars=Pillar.objects.all(), severities=Severity.choices,
                   statuses=Finding.Status.choices, params=self.request.GET,
                   qs=query.urlencode())
        return ctx


class FindingDetailView(LoginRequiredMixin, DetailView):
    model = Finding
    template_name = 'findings/finding_detail.html'

    def get_queryset(self):
        return Finding.objects.select_related('technique__pillar', 'data_source',
                                              'reported_by').prefetch_related('tasks__assignee')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['can_write'] = user.has_role(*WRITE_ROLES)
        ctx['can_update_task'] = user.has_role('admin', 'analyst', 'devops')
        ctx['task_form'] = TaskForm()
        ctx['task_statuses'] = RemediationTask.Status.choices
        return ctx


class FindingCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = WRITE_ROLES
    model = Finding
    form_class = FindingForm
    template_name = 'findings/finding_form.html'

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        response = super().form_valid(form)
        record(self.request, 'finding_created', f'finding {self.object.pk}')
        messages.success(self.request, 'Finding raised.')
        return response


class FindingUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = WRITE_ROLES
    model = Finding
    form_class = FindingForm
    template_name = 'findings/finding_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        record(self.request, 'finding_updated', f'finding {self.object.pk}')
        messages.success(self.request, 'Finding updated.')
        return response


class TaskCreateView(RoleRequiredMixin, View):
    allowed_roles = WRITE_ROLES

    def post(self, request, pk):
        finding = get_object_or_404(Finding, pk=pk)
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.finding = finding
            task.save()
            record(request, 'task_created', f'finding {finding.pk}')
            messages.success(request, 'Remediation task assigned.')
        else:
            messages.error(request, 'Could not create the task. Check the form.')
        return redirect(reverse('finding-detail', args=[pk]))


class TaskStatusView(RoleRequiredMixin, View):
    allowed_roles = ('admin', 'analyst', 'devops')

    def post(self, request, pk):
        task = get_object_or_404(RemediationTask, pk=pk)
        status = request.POST.get('status')
        if status in RemediationTask.Status.values:
            task.status = status
            task.save(update_fields=['status'])
            record(request, 'task_status', f'task {task.pk} -> {status}')
        return redirect(reverse('finding-detail', args=[task.finding_id]))


def _safe_cell(value):
    """Neutralise spreadsheet formula injection in exported CSV cells."""
    text = str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@', '\t', '\r') else text


class FindingExportView(RoleRequiredMixin, View):
    allowed_roles = ('admin', 'analyst', 'auditor')

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="findings.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Pillar', 'Technique', 'Severity', 'Score',
                         'Status', 'Detected', 'Incident', 'Asset'])
        for f in filtered_findings(request.GET):
            writer.writerow([_safe_cell(v) for v in (
                f.pk, f.title, f.pillar.name, f.technique.name, f.severity, f.score,
                f.get_status_display(), f.detected_at.strftime('%Y-%m-%d %H:%M'),
                f.incident_ref, f.affected_asset)])
        record(request, 'findings_exported')
        return response
