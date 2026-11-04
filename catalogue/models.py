from django.db import models


class Severity(models.TextChoices):
    CRITICAL = 'Critical', 'Critical'
    HIGH = 'High', 'High'
    MEDIUM = 'Medium', 'Medium'
    LOW = 'Low', 'Low'


class Pillar(models.Model):
    """One of the five SITF pillars of the code factory."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Technique(models.Model):
    """An attack technique catalogued against a pillar."""

    sitf_id = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.PROTECT, related_name='techniques')
    base_severity = models.CharField(max_length=10, choices=Severity.choices,
                                     default=Severity.MEDIUM)

    class Meta:
        ordering = ['pillar__order', 'sitf_id']

    def __str__(self):
        return f'{self.sitf_id} {self.name}'
