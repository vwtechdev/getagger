from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from apps.invoices.services import InvoiceService
from apps.labels.services import LabelService


@login_required
def part_labels_pdf(request, pk):
    """RF-06: PDF com 1 etiqueta por peça associada à NF."""
    invoice = InvoiceService.get_for_technician(pk, request.user)
    pdf = LabelService.generate_part_labels_pdf(invoice)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="etiquetas_pecas_{invoice.number}.pdf"'
    return resp


@login_required
def reprint(request):
    """RF-07: reimpressão de etiquetas (peças e romaneio) do técnico.

    Só mostra NFs que possuem ao menos uma peça associada.
    """
    invoices = InvoiceService.list_with_associations_by_technician(request.user)
    return render(request, 'labels/reprint.html', {'invoices': invoices})
