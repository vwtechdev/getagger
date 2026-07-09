from django import forms


class InvoiceImportForm(forms.Form):
    TYPE_CHOICES = [
        ('outgoing', 'NF de Saída'),
        ('incoming', 'NF de Entrada'),
    ]

    tipo = forms.ChoiceField(
        choices=TYPE_CHOICES, label='Tipo de Nota Fiscal',
        widget=forms.Select(attrs={'class': 'form-control', 'x-model': 'tipo'}),
    )
    arquivo = forms.FileField(
        label='Arquivo PDF',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control', 'accept': 'application/pdf',
        }),
    )