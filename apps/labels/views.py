import calendar

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.invoices.services import InvoiceService
from apps.labels.models import LabelSettings
from apps.labels.services import LabelService

LabelSettingsForm = forms.modelform_factory(
    LabelSettings,
    fields=['page_format', 'margin', 'font_size'],
    widgets={
        'page_format': forms.Select(attrs={'class': 'form-select'}),
        'margin': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        'font_size': forms.NumberInput(attrs={'class': 'form-control'}),
    },
)


@login_required
def part_labels_pdf(request, pk):
    """RF-06: PDF com 1 etiqueta por peça associada à NF."""
    invoice = InvoiceService.get_for_technician(pk, request.user)
    settings = LabelService.get_settings(request.user)
    pdf = LabelService.generate_part_labels_pdf(invoice, settings)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="etiquetas_pecas_{invoice.number}.pdf"'
    return resp


@login_required
def reprint(request):
    """RF-07: reimpressão de etiquetas (peças e romaneio) do técnico.

    Só mostra NFs que possuem ao menos uma peça associada.
    """
    qs = InvoiceService.list_with_associations_by_technician(request.user)
    q = request.GET.get('q', '').strip()
    today = timezone.localdate()
    default_from = today.replace(day=1).isoformat()
    default_to = today.replace(day=calendar.monthrange(today.year, today.month)[1]).isoformat()
    date_from = request.GET['date_from'].strip() if 'date_from' in request.GET else default_from
    date_to = request.GET['date_to'].strip() if 'date_to' in request.GET else default_to
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(return_code__icontains=q))
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    return render(request, 'labels/reprint.html', {
        'invoices': qs, 'q': q, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def label_settings(request):
    settings = LabelService.get_settings(request.user)
    form = LabelSettingsForm(request.POST or None, instance=settings)
    if form.is_valid():
        form.save()
        messages.success(request, 'Configurações Salvas')
        return redirect('labels:label_settings')
    return render(request, 'labels/label_settings.html', {'form': form})
