from django import forms

from apps.services.models import ServiceCall


class ServiceCallForm(forms.ModelForm):
    """Form de atendimento. ``date`` e ``technician`` tratados no serviço."""

    class Meta:
        model = ServiceCall
        fields = ['ticket_number', 'part_name', 'defect', 'date']
        widgets = {
            'ticket_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: 12345'}),
            'part_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex.: SSD, HD, Fonte...',
            }),
            'defect': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Defeito informado'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
