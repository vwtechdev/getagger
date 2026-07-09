from apps.labels.models import InvoiceLabel, PartLabel


class PartLabelRepository:
    @staticmethod
    def for_incoming_invoice(invoice):
        return PartLabel.objects.filter(
            service_call__destination_invoice=invoice
        ).select_related('service_call')

    @staticmethod
    def for_technician(technician):
        return PartLabel.objects.filter(
            service_call__technician=technician
        ).select_related('service_call')


class InvoiceLabelRepository:
    @staticmethod
    def for_invoice(invoice):
        return invoice.labels.all()

    @staticmethod
    def for_technician(technician):
        return InvoiceLabel.objects.filter(
            invoice__technician=technician
        ).select_related('invoice')