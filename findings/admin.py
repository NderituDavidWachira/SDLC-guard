from django.contrib import admin

from .models import Finding, RemediationTask

admin.site.register(Finding)
admin.site.register(RemediationTask)
