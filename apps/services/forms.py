from django import forms
from django.utils import timezone

from apps.services.models import ServiceCall


class ServiceCallForm(forms.ModelForm):
    """Form de atendimento. ``date`` e ``technician`` tratados no serviço."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].required = False

    def clean_date(self):
        return self.cleaned_data.get('date') or timezone.localdate()

    class Meta:
        model = ServiceCall
        fields = ['ticket_number', 'serial_number', 'part_name', 'defect', 'date']
        widgets = {
            'ticket_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: 12345'}),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escaneie ou digite o nº de série',
                'inputmode': 'url',
                'autocomplete': 'off',
            }),
            'part_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex.: SSD, HD, Fonte...',
            }),
            'defect': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Defeito informado'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }
