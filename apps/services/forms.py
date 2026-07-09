from django import forms
from django.utils import timezone

from apps.services.models import ServiceCall


class ServiceCallForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.technician = kwargs.pop('technician', None)
        super().__init__(*args, **kwargs)
        self.fields['date'].required = False

        if self.instance.pk and self.instance.source_invoice_id:
            self.fields['part_name'].widget = forms.TextInput(attrs={
                'class': 'form-control', 'readonly': True,
            })

    source_invoice_number = forms.CharField(
        label='Número da NF de saída',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: 123456'}),
    )
    quantity = forms.IntegerField(
        label='Quantidade',
        required=False,
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    def clean_date(self):
        return self.cleaned_data.get('date') or timezone.localdate()

    class Meta:
        model = ServiceCall
        fields = ['ticket_number', 'serial_number', 'part_name', 'defect', 'date', 'source_invoice_number', 'quantity']
        widgets = {
            'ticket_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: 12345'}),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escaneie ou digite o nº de série',
                'inputmode': 'url',
                'autocomplete': 'off',
            }),
            'part_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: SSD, HD, Fonte...'}),
            'defect': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Defeito informado'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }