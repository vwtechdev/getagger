"""Casos de uso de Associação (RF-05). SEMPRE manual — RN-05, RN-06.

Nenhum método compara/infer ``part_name``. O usuário informa explicitamente
item_id + service_call_id no drag & drop.
"""
from apps.associations.repositories import AssociationRepository
from apps.invoices.models import InvoiceItem
from apps.invoices.repositories import InvoiceItemRepository
from apps.services.models import ServiceCall
from apps.services.repositories import ServiceCallRepository


class AssociationService:
    @staticmethod
    def list_for_invoice(invoice):
        return AssociationRepository.for_invoice(invoice)

    @staticmethod
    def pending_items(invoice):
        """Itens da NF ainda não associados (não usa part_name — RN-05)."""
        return InvoiceItemRepository.pending_for_invoice(invoice)

    @staticmethod
    def available_service_calls(technician, invoice):
        """Atendimentos do técnico ainda não associados a item algum."""
        associated = AssociationRepository.for_invoice(invoice).values_list(
            'service_call_id', flat=True
        )
        return (
            ServiceCallRepository.for_technician(technician)
            .exclude(pk__in=list(associated))
            .order_by('-date', '-created_at')
        )

    @staticmethod
    def counters(invoice, technician):
        total_items = invoice.items.count()
        associated = AssociationRepository.for_invoice(invoice).count()
        pending = max(total_items - associated, 0)
        remaining = AssociationService.available_service_calls(
            technician, invoice
        ).count()
        return {
            'pending': pending,
            'associated': associated,
            'remaining': remaining,
            'total_items': total_items,
        }

    @staticmethod
    def create(*, item_id, service_call_id, technician):
        """Cria vínculo permanente (RN-06). Valida posse pelo técnico (RN-04).

        Após associar, arquiva o ServiceCall (não aparece mais na lista de
        peças disponíveis). O arquivamento é revertido ao desfazer.
        """
        service_call = ServiceCallRepository.get_for_technician(service_call_id, technician)
        item = _item_for_technician(item_id, technician)
        if AssociationRepository.for_invoice(item.invoice).filter(
            service_call=service_call
        ).exists():
            raise ValueError('Atendimento já associado a um item desta NF.')
        association = AssociationRepository.create(
            service_call=service_call, invoice_item=item
        )
        service_call.archive()
        return association

    @staticmethod
    def undo(association_id, technician):
        """Desfaz associação: remove vínculo e desarquiva o ServiceCall."""
        association = AssociationRepository.get_for_technician(association_id, technician)
        service_call = association.service_call
        AssociationRepository.delete(association)
        service_call.unarchive()


def _item_for_technician(item_id, technician):
    """Retorna InvoiceItem pertencente a uma NF do técnico (RN-04)."""
    return InvoiceItem.objects.select_related('invoice').get(
        pk=item_id, invoice__technician=technician
    )
