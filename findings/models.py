from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from catalogue.models import Severity, Technique
from sources.models import DataSource

from .services import classify_severity


class Finding(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        INVESTIGATING = 'investigating', 'Investigating'
        RESOLVED = 'resolved', 'Resolved'
        FALSE_POSITIVE = 'false_positive', 'False positive'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    technique = models.ForeignKey(Technique, on_delete=models.PROTECT, related_name='findings')
    data_source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name='findings')
    score = models.FloatField(default=5.0,
                              validators=[MinValueValidator(0), MaxValueValidator(10)])
    severity = models.CharField(max_length=10, choices=Severity.choices, editable=False)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    detected_at = models.DateTimeField(default=timezone.now)
    incident_ref = models.CharField(max_length=30, blank=True)
    affected_asset = models.CharField(max_length=150, blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='reported_findings')

    class Meta:
        ordering = ['-detected_at']

    @property
    def pillar(self):
        return self.technique.pillar

    @property
    def is_open(self):
        return self.status in ('open', 'investigating')

    def get_absolute_url(self):
        return reverse('finding-detail', args=[self.pk])

    def save(self, *args, **kwargs):
        self.severity = classify_severity(self.score)  # severity is always derived
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class RemediationTask(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'To do'
        IN_PROGRESS = 'in_progress', 'In progress'
        DONE = 'done', 'Done'

    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='tasks')
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.TODO)
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f'Task for {self.finding_id}'
