"""Casos de uso do módulo de Nota Fiscal (RF-04).

Isolamento por técnico (RN-04). O PDF não é persistido — apenas extraído.
"""
from django.db import transaction

from apps.invoices import invoice_importer
from apps.invoices.models import InvoiceItem
from apps.invoices.repositories import InvoiceRepository


class InvoiceService:
    @staticmethod
    def list_by_technician(technician):
        return InvoiceRepository.for_technician(technician)

    @staticmethod
    def list_with_associations_by_technician(technician):
        """NFs que possuem ao menos uma peça associada (para reimpressão)."""
        return InvoiceRepository.for_technician(technician).filter(
            items__association__isnull=False
        ).distinct()

    @staticmethod
    def get_for_technician(pk, technician):
        return InvoiceRepository.get_for_technician(pk, technician)

    @staticmethod
    def import_invoice(technician, *, upload, volumes=1):
        """Importa PDF: extrai tabela + NF-e + Código Devolução (RN-13),
        cria a Invoice, os itens e as etiquetas romaneio (1 por volume).

        ``upload`` é lido em memória e NÃO é persistido.
        """
        upload.seek(0)
        data = invoice_importer.extract_invoice(upload)

        invoice = InvoiceRepository.create(
            technician=technician,
            number=data['number'],
            return_code=data['return_code'],
            volumes=volumes,
        )
        for item in data['items']:
            InvoiceItem.objects.create(
                invoice=invoice,
                product_code=item['product_code'],
                description=item['description'],
            )

        # Romaneio: 1 etiqueta por volume (RN-11/RN-12) — delega ao app labels.
        from apps.labels.services import LabelService
        LabelService.ensure_invoice_labels(invoice)
        return invoice

    @staticmethod
    @transaction.atomic
    def delete(pk, technician):
        """Exclui NF e registros relacionados, desarquivando ServiceCalls."""
        invoice = InvoiceRepository.get_for_technician(pk, technician)

        from apps.associations.models import Association
        from apps.labels.models import InvoiceLabel, PartLabel

        for assoc in Association.objects.filter(invoice_item__invoice=invoice):
            PartLabel.objects.filter(association=assoc).delete()
            assoc.service_call.unarchive()
            assoc.delete()

        InvoiceLabel.objects.filter(invoice=invoice).delete()
        InvoiceItem.objects.filter(invoice=invoice).delete()
        invoice.archive()
