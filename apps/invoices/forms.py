from django import forms


class InvoiceImportForm(forms.Form):
    """Importação de NF (RF-04). Volumes com default 1 (RN-12). PDF não persistido."""

    arquivo = forms.FileField(
        label='Arquivo PDF',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf',
        }),
    )
    volumes = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Quantidade de volumes',
        help_text='Default 1. Gera 1 etiqueta romaneio por volume (1/N..N/N).',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
