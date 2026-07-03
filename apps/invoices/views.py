from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.invoices.forms import InvoiceImportForm
from apps.invoices.services import InvoiceService


@login_required
def invoice_list(request):
    invoices = InvoiceService.list_by_technician(request.user)
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})


@login_required
def invoice_import(request):
    form = InvoiceImportForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        try:
            invoice = InvoiceService.import_invoice(
                technician=request.user,
                upload=form.cleaned_data['arquivo'],
                volumes=form.cleaned_data['volumes'],
            )
            messages.success(request, f'NF-e {invoice.number} importada.')
            return redirect('associations:association', pk=invoice.pk)
        except Exception as exc:
            messages.error(request, f'Falha ao importar NF: {exc}')
    return render(request, 'invoices/invoice_import.html', {'form': form})


@login_required
def invoice_detail(request, pk):
    invoice = InvoiceService.get_for_technician(pk, request.user)
    items = invoice.items.all()
    from apps.labels.services import LabelService
    romaneios = LabelService.list_invoice_labels(invoice)
    return render(
        request,
        'invoices/invoice_detail.html',
        {'invoice': invoice, 'items': items, 'romaneios': romaneios},
    )


@login_required
def invoice_labels_pdf(request, pk):
    """RF-08/RF-07: PDF separado das etiquetas romaneio (download/reimpressão)."""
    invoice = InvoiceService.get_for_technician(pk, request.user)
    from apps.labels.services import LabelService
    pdf = LabelService.generate_invoice_labels_pdf(invoice)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="romaneio_{invoice.number}.pdf"'
    return resp
