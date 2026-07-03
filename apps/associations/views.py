from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.associations.services import AssociationService
from apps.invoices.services import InvoiceService


def _board_context(request, invoice):
    return {
        'invoice': invoice,
        'items': AssociationService.pending_items(invoice),
        'service_calls': AssociationService.available_service_calls(request.user, invoice),
        'associations': AssociationService.list_for_invoice(invoice),
        'counters': AssociationService.counters(invoice, request.user),
    }

@login_required
def association(request, pk):
    """RF-05: tela de associação visual (drag & drop). Manual (RN-06)."""
    invoice = InvoiceService.get_for_technician(pk, request.user)
    return render(request, 'associations/association.html', _board_context(request, invoice))


@login_required
def association_create(request, pk):
    """Endpoint HTMX: cria vínculo manual (item_id + service_call_id). RN-06."""
    invoice = InvoiceService.get_for_technician(pk, request.user)
    if request.method == 'POST':
        try:
            AssociationService.create(
                item_id=request.POST.get('item_id'),
                service_call_id=request.POST.get('service_call_id'),
                technician=request.user,
            )
        except Exception as exc:
            messages.error(request, f'Não foi possível associar: {exc}')
    return render(request, 'associations/association_board.html', _board_context(request, invoice))


@login_required
def association_undo(request, pk):
    """Endpoint HTMX: desfaz associação (libera item e atendimento)."""
    invoice = InvoiceService.get_for_technician(pk, request.user)
    if request.method == 'POST':
        try:
            AssociationService.undo(request.POST.get('association_id'), request.user)
        except Exception as exc:
            messages.error(request, f'Não foi possível desfazer: {exc}')
    return render(request, 'associations/association_board.html', _board_context(request, invoice))
