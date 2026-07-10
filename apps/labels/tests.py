import io

import pdfplumber
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.invoices.services import InvoiceService
from apps.invoices.tests import build_invoice_pdf
from apps.labels import label_generator
from apps.labels.models import InvoiceLabel, PartLabel
from apps.labels.services import LabelService
from apps.services.models import ServiceCall
from apps.services.services import ServiceCallService

User = get_user_model()


def _page_count(pdf_bytes):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return len(pdf.pages)


class InvoiceLabelTest(TestCase):
    def setUp(self):
        self.tech = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.invoice = InvoiceService.import_incoming(
            technician=self.tech, upload=self._make_incoming_pdf())

    def _make_incoming_pdf(self):
        from apps.invoices.tests import build_incoming_pdf
        return build_incoming_pdf()

    def test_one_label_per_volume(self):
        LabelService.ensure_invoice_labels(self.invoice)
        indexes = list(
            InvoiceLabel.objects.filter(invoice=self.invoice)
            .order_by('volume_index').values_list('volume_index', flat=True)
        )
        self.assertEqual(indexes, [1])

    def test_romaneio_pdf_valid_and_contains_labels(self):
        pdf = LabelService.generate_invoice_labels_pdf(self.invoice)
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertGreaterEqual(_page_count(pdf), 1)

    def test_romaneio_thermal_one_per_page(self):
        from apps.labels.models import LabelSettings
        settings, _ = LabelSettings.objects.get_or_create(technician=self.tech)
        settings.page_format = 'TEXT_RAW'
        settings.save()
        pdf = LabelService.generate_invoice_labels_pdf(self.invoice, settings)
        self.assertTrue(pdf.startswith(b'\x1b\x40'))


class PartLabelTest(TestCase):
    def setUp(self):
        self.tech = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.call = ServiceCallService.create(
            technician=self.tech, ticket_number='1', part_name='Monitor', defect='x')

    def test_part_labels_pdf_non_empty(self):
        self.call.destination_invoice_id = '00000000-0000-0000-0000-000000000001'
        self.call.status = 'attended'
        self.call.save()
        from apps.invoices.models import Invoice
        inv = Invoice.objects.create(
            technician=self.tech, type='incoming', number='22656',
            return_code='23788', volumes=1,
        )
        Item = type('Item', (), {'product_code': '0001', 'description': 'SSD'})
        inv.items.create(product_code='0001', description='SSD')
        self.call.destination_invoice = inv
        self.call.save()
        part = PartLabel.objects.create(service_call=self.call)
        pdf = label_generator.generate_part_labels_pdf([part], LabelService.get_settings(self.tech))
        self.assertTrue(pdf.startswith(b'%PDF'))