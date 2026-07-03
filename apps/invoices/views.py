import calendar

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.invoices.forms import InvoiceImportForm
from apps.invoices.services import InvoiceService


def _month_range():
    today = timezone.localdate()
    return (
        today.replace(day=1).isoformat(),
        today.replace(day=calendar.monthrange(today.year, today.month)[1]).isoformat(),
    )

@login_required
def invoice_list(request):
    qs = InvoiceService.list_by_technician(request.user)
    q = request.GET.get('q', '').strip()
    default_from, default_to = _month_range()
    date_from = request.GET['date_from'].strip() if 'date_from' in request.GET else default_from
    date_to = request.GET['date_to'].strip() if 'date_to' in request.GET else default_to
    if q:
        qs = qs.filter(
            Q(number__icontains=q) | Q(return_code__icontains=q)
        )
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    return render(request, 'invoices/invoice_list.html', {
        'invoices': qs, 'q': q, 'date_from': date_from, 'date_to': date_to,
    })


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
@require_POST
def invoice_delete(request, pk):
    try:
        InvoiceService.delete(pk, request.user)
        messages.success(request, 'Nota fiscal excluída.')
    except Exception as exc:
        messages.error(request, f'Erro ao excluir NF: {exc}')
    return redirect('invoices:invoice_list')


@login_required
def invoice_labels_pdf(request, pk):
    """RF-08/RF-07: PDF separado das etiquetas romaneio (download/reimpressão)."""
    invoice = InvoiceService.get_for_technician(pk, request.user)
    from apps.labels.services import LabelService
    settings = LabelService.get_settings(request.user)
    pdf = LabelService.generate_invoice_labels_pdf(invoice, settings)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="romaneio_{invoice.number}.pdf"'
    return resp
