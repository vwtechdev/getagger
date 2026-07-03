"""Repository — acesso a dados isolado por técnico (RN-04)."""
from apps.invoices.models import Invoice, InvoiceItem


class InvoiceRepository:
    @staticmethod
    def for_technician(technician):
        return Invoice.objects.filter(technician=technician, archived_at__isnull=True)

    @staticmethod
    def get_for_technician(pk, technician):
        return InvoiceRepository.for_technician(technician).get(pk=pk)

    @staticmethod
    def create(technician, *, number, return_code, volumes=1):
        return Invoice.objects.create(
            technician=technician,
            number=number,
            return_code=return_code,
            volumes=volumes,
        )


class InvoiceItemRepository:
    @staticmethod
    def for_invoice(invoice):
        return invoice.items.filter(archived_at__isnull=True)

    @staticmethod
    def pending_for_invoice(invoice):
        """Itens ainda não associados (não usa part_name — RN-05)."""
        from apps.associations.models import Association
        associated = Association.objects.filter(
            invoice_item__invoice=invoice
        ).values_list('invoice_item_id', flat=True)
        return invoice.items.exclude(pk__in=associated)
