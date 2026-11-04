from django import forms
from django.contrib.auth import get_user_model

from .models import Finding, RemediationTask


class FindingForm(forms.ModelForm):
    class Meta:
        model = Finding
        fields = ['title', 'description', 'technique', 'data_source', 'score',
                  'status', 'incident_ref', 'affected_asset']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(required=False,
                               widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = RemediationTask
        fields = ['assignee', 'due_date', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignee'].queryset = get_user_model().objects.filter(
            is_active=True, role__in=['devops', 'analyst'])
