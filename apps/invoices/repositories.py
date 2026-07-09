from apps.invoices.models import Invoice, InvoiceItem


class InvoiceRepository:
    @staticmethod
    def for_technician(technician):
        return Invoice.objects.filter(technician=technician, archived_at__isnull=True)

    @staticmethod
    def get_for_technician(pk, technician):
        return InvoiceRepository.for_technician(technician).get(pk=pk)

    @staticmethod
    def create(technician, *, type, number, return_code='', volumes=1):
        return Invoice.objects.create(
            technician=technician, type=type, number=number,
            return_code=return_code, volumes=volumes,
        )


class InvoiceItemRepository:
    @staticmethod
    def for_invoice(invoice):
        return invoice.items.filter(archived_at__isnull=True)