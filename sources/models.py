from django.db import models

from catalogue.models import Pillar


class DataSource(models.Model):
    """A system that supplies events/findings (GitHub, CI server, registry...)."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=30)
    pillar = models.ForeignKey(Pillar, on_delete=models.PROTECT, related_name='sources')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
