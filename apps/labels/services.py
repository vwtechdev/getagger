from apps.labels import label_generator
from apps.labels.models import InvoiceLabel, LabelSettings, PartLabel
from apps.labels.repositories import InvoiceLabelRepository, PartLabelRepository


class LabelService:
    @staticmethod
    def get_settings(technician):
        settings, _ = LabelSettings.objects.get_or_create(technician=technician)
        return settings

    @staticmethod
    def ensure_invoice_labels(invoice):
        total = max(int(invoice.volumes or 1), 1)
        InvoiceLabel.objects.filter(invoice=invoice).delete()
        for index in range(1, total + 1):
            InvoiceLabel.objects.create(invoice=invoice, volume_index=index)

    @staticmethod
    def list_invoice_labels(invoice):
        return InvoiceLabelRepository.for_invoice(invoice)

    @staticmethod
    def generate_invoice_labels_pdf(invoice, settings=None):
        if settings is None:
            settings = LabelService.get_settings(invoice.technician)
        return label_generator.generate_invoice_labels_pdf(invoice, settings)

    @staticmethod
    def ensure_part_labels_for_incoming(invoice):
        """Garante 1 PartLabel por ServiceCall vinculado à NF de entrada."""
        existing = set(
            PartLabelRepository.for_incoming_invoice(invoice).values_list('service_call_id', flat=True)
        )
        for call in invoice.destination_calls.all():
            if call.pk not in existing:
                PartLabel.objects.create(service_call=call)
        return PartLabelRepository.for_incoming_invoice(invoice)

    @staticmethod
    def generate_part_labels_pdf_for_incoming(invoice, settings=None, title='ETIQUETA DE DEFEITO'):
        etiquetas = LabelService.ensure_part_labels_for_incoming(invoice)
        if settings is None:
            settings = LabelService.get_settings(invoice.technician)
        return label_generator.generate_part_labels_pdf(etiquetas, settings, title)

    @staticmethod
    def generate_combined_labels_pdf(invoice, settings=None):
        if settings is None:
            settings = LabelService.get_settings(invoice.technician)
        LabelService.ensure_invoice_labels(invoice)
        part_labels = list(LabelService.ensure_part_labels_for_incoming(invoice))
        return label_generator.generate_combined_labels_pdf(invoice, part_labels, settings)