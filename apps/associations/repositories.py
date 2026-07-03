"""Repository — acesso a dados isolado por técnico (RN-04)."""
from apps.associations.models import Association


class AssociationRepository:
    @staticmethod
    def for_invoice(invoice):
        return Association.objects.filter(
            invoice_item__invoice=invoice
        ).select_related('service_call', 'invoice_item')

    @staticmethod
    def get_for_technician(pk, technician):
        return Association.objects.get(pk=pk, service_call__technician=technician)

    @staticmethod
    def create(*, service_call, invoice_item):
        return Association.objects.create(
            service_call=service_call, invoice_item=invoice_item
        )

    @staticmethod
    def delete(association):
        association.delete()
