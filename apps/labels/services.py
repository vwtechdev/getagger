"""Casos de uso de Etiquetas (RF-06, RF-08).

- PartLabel: 1 por peça (por associação).
- InvoiceLabel: 1 por volume (romaneio), numeradas 1/N..N/N (RN-11/RN-12).
"""
from apps.associations.repositories import AssociationRepository
from apps.labels import label_generator
from apps.labels.models import InvoiceLabel, PartLabel
from apps.labels.repositories import InvoiceLabelRepository, PartLabelRepository


class LabelService:
    # -------------------------------------------------- Romaneio (InvoiceLabel)
    @staticmethod
    def ensure_invoice_labels(invoice):
        """Cria 1 InvoiceLabel por volume — RN-11/RN-12. (Re)cria a partir de 1..N."""
        total = max(int(invoice.volumes or 1), 1)
        InvoiceLabel.objects.filter(invoice=invoice).delete()
        for index in range(1, total + 1):
            InvoiceLabel.objects.create(invoice=invoice, volume_index=index)

    @staticmethod
    def list_invoice_labels(invoice):
        return InvoiceLabelRepository.for_invoice(invoice)

    @staticmethod
    def generate_invoice_labels_pdf(invoice):
        """PDF (bytes) com as etiquetas romaneio, em PDF separado (RN-11/RN-12)."""
        return label_generator.generate_invoice_labels_pdf(invoice)

    # ----------------------------------------------------- Peças (PartLabel)
    @staticmethod
    def ensure_part_labels(invoice):
        """Garante 1 PartLabel por associação da NF e retorna o queryset."""
        existing = set(
            PartLabelRepository.for_invoice(invoice).values_list('association_id', flat=True)
        )
        for assoc in AssociationRepository.for_invoice(invoice):
            if assoc.pk not in existing:
                PartLabel.objects.create(association=assoc)
        return PartLabelRepository.for_invoice(invoice)

    @staticmethod
    def generate_part_labels_pdf(invoice):
        etiquetas = LabelService.ensure_part_labels(invoice)
        return label_generator.generate_part_labels_pdf(etiquetas)
