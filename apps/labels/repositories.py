"""Repository — acesso a dados isolado por técnico (RN-04)."""
from apps.associations.models import Association
from apps.labels.models import InvoiceLabel, PartLabel


class PartLabelRepository:
    @staticmethod
    def for_invoice(invoice):
        return PartLabel.objects.filter(
            association__invoice_item__invoice=invoice
        ).select_related('association__service_call', 'association__invoice_item')

    @staticmethod
    def for_technician(technician):
        return PartLabel.objects.filter(
            association__service_call__technician=technician
        ).select_related('association__service_call', 'association__invoice_item')


class InvoiceLabelRepository:
    @staticmethod
    def for_invoice(invoice):
        return invoice.labels.all()

    @staticmethod
    def for_technician(technician):
        return InvoiceLabel.objects.filter(
            invoice__technician=technician
        ).select_related('invoice')
