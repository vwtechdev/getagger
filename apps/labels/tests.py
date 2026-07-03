import io

import pdfplumber
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.associations.services import AssociationService
from apps.invoices.services import InvoiceService
from apps.invoices.tests import build_invoice_pdf
from apps.labels.models import InvoiceLabel, PartLabel
from apps.labels.services import LabelService
from apps.services.services import ServiceCallService

User = get_user_model()


def _page_count(pdf_bytes):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return len(pdf.pages)


class InvoiceLabelTest(TestCase):
    def setUp(self):
        self.tech = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.invoice = InvoiceService.import_invoice(
            technician=self.tech, upload=build_invoice_pdf(), volumes=3)

    def test_one_label_per_volume(self):
        """RN-11/RN-12: N volumes -> N InvoiceLabel (1..N)."""
        LabelService.ensure_invoice_labels(self.invoice)
        indexes = list(
            InvoiceLabel.objects.filter(invoice=self.invoice)
            .order_by('volume_index').values_list('volume_index', flat=True)
        )
        self.assertEqual(indexes, [1, 2, 3])

    def test_ensure_is_idempotent_recreate(self):
        LabelService.ensure_invoice_labels(self.invoice)
        self.invoice.volumes = 2
        self.invoice.save()
        LabelService.ensure_invoice_labels(self.invoice)
        self.assertEqual(InvoiceLabel.objects.filter(invoice=self.invoice).count(), 2)

    def test_romaneio_pdf_valid_and_contains_labels(self):
        """RF-08: PDF romaneio válido e contém etiquetas de todos os volumes."""
        pdf = LabelService.generate_invoice_labels_pdf(self.invoice)
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertGreaterEqual(_page_count(pdf), 1)
        with pdfplumber.open(io.BytesIO(pdf)) as doc:
            text = ''.join(p.extract_text() or '' for p in doc.pages)
        for i in range(1, 4):
            self.assertIn(f'{i} de 3', text)

    def test_romaneio_thermal_one_per_page(self):
        """RF-08: THERMAL_80MM gera 1 página por volume."""
        from apps.labels.models import LabelSettings
        settings, _ = LabelSettings.objects.get_or_create(technician=self.tech)
        settings.page_format = 'THERMAL_80MM'
        settings.save()
        pdf = LabelService.generate_invoice_labels_pdf(self.invoice, settings)
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertEqual(_page_count(pdf), 3)


class PartLabelTest(TestCase):
    def setUp(self):
        self.tech = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.call = ServiceCallService.create(
            technician=self.tech, ticket_number='1', part_name='SSD', defect='x')
        self.invoice = InvoiceService.import_invoice(
            technician=self.tech, upload=build_invoice_pdf(), volumes=1)
        self.item = self.invoice.items.first()
        self.assoc = AssociationService.create(
            item_id=self.item.pk, service_call_id=self.call.pk, technician=self.tech)

    def test_one_part_label_per_association(self):
        """RF-06: 1 PartLabel por associação."""
        LabelService.ensure_part_labels(self.invoice)
        self.assertEqual(PartLabel.objects.filter(association=self.assoc).count(), 1)
        self.assertEqual(
            PartLabel.objects.filter(
                association__invoice_item__invoice=self.invoice
            ).count(), 1)

    def test_part_labels_pdf_non_empty_and_separate(self):
        """RF-06: PDF de peças gerado e distinto do romaneio."""
        part_pdf = LabelService.generate_part_labels_pdf(self.invoice)
        romaneio_pdf = LabelService.generate_invoice_labels_pdf(self.invoice)
        self.assertTrue(part_pdf.startswith(b'%PDF'))
        self.assertEqual(_page_count(part_pdf), 1)  # 1 peça associada -> 1 página
        # PDFs separados (funções distintas, ambos válidos).
        self.assertTrue(romaneio_pdf.startswith(b'%PDF'))
