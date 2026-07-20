import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.invoices import invoice_importer
from apps.invoices.models import Invoice, InvoiceItem
from apps.invoices.services import InvoiceService
from apps.labels.models import InvoiceLabel

User = get_user_model()


def build_invoice_pdf(number='22656', return_code='23788', include_labels=True):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    flow = []
    if include_labels:
        flow.append(Paragraph(f'NÚMERO {number}', styles['Normal']))
        flow.append(Paragraph('1', styles['Normal']))
        flow.append(Paragraph('SÉRIE', styles['Normal']))
        flow.append(Paragraph('DANFE', styles['Normal']))
        flow.append(Paragraph(f'Observacao: Codigo Devolucao: {return_code}', styles['Normal']))
        flow.append(Spacer(1, 12))
    flow.append(Paragraph('DADOS DOS PRODUTOS / SERVIÇOS', styles['Heading2']))
    flow.append(Spacer(1, 6))
    table = Table([
        ['CÓD. PROD', 'DESCRIÇÃO DOS PRODUTOS / SERVIÇOS', 'NCM', 'CFOP', 'QTD'],
        ['0001', 'SSD NVMe 1TB', '84717000', '5405', '1'],
        ['0002', 'Memória DDR4 16GB', '84733000', '5405', '1'],
        ['0003', 'Fonte ATX 650W', '85044000', '5405', '1'],
    ])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    flow.append(table)
    doc.build(flow)
    buf.seek(0)
    return buf


def build_incoming_pdf(number='22823', return_code='23734', volumes=1, retorno_refs='22656'):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    flow = []
    flow.append(Paragraph(f'NÚMERO {number}', styles['Normal']))
    flow.append(Paragraph('1', styles['Normal']))
    flow.append(Paragraph('SÉRIE', styles['Normal']))
    flow.append(Paragraph('DANFE', styles['Normal']))
    flow.append(Paragraph(f'TRANSPORTADOR / VOLUME QUANTIDADE {volumes}', styles['Normal']))
    flow.append(Paragraph(f'Observacao: Codigo Devolucao: {return_code}', styles['Normal']))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph('DADOS DOS PRODUTOS / SERVIÇOS', styles['Heading2']))
    flow.append(Spacer(1, 6))
    table = Table([
        ['CÓD. PROD', 'DESCRIÇÃO DOS PRODUTOS / SERVIÇOS', 'NCM', 'CFOP', 'QTD'],
        ['0001', 'SSD NVMe 1TB', '84717000', '5405', '1'],
        ['0002', 'Memória DDR4 16GB', '84733000', '5405', '1'],
        ['0003', 'Fonte ATX 650W', '85044000', '5405', '1'],
    ])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    flow.append(table)
    flow.append(Paragraph('DADOS ADICIONAIS', styles['Heading2']))
    flow.append(Paragraph(f'RETORNO REF. NF..: {retorno_refs}', styles['Normal']))
    doc.build(flow)
    buf.seek(0)
    return buf


class InvoiceImporterTest(TestCase):
    def test_extract_fixed_labels_and_items(self):
        data = invoice_importer.extract_outgoing(build_invoice_pdf())
        self.assertEqual(data['number'], '22656')
        codes = [i['product_code'] for i in data['items']]
        descs = [i['description'] for i in data['items']]
        self.assertEqual(codes, ['0001', '0002', '0003'])
        self.assertIn('SSD NVMe 1TB', descs)
        self.assertIn('quantity', data['items'][0])

    def test_extract_incoming(self):
        data = invoice_importer.extract_incoming(build_incoming_pdf())
        self.assertEqual(data['number'], '22823')
        self.assertEqual(data['return_code'], '23734')
        self.assertIn('22656', data.get('retorno_refs', []))

    def test_missing_labels_raises(self):
        buf = build_invoice_pdf(include_labels=False)
        with self.assertRaises(invoice_importer.InvoiceImportError):
            invoice_importer.extract_outgoing(buf)


class InvoiceServiceTest(TestCase):
    def setUp(self):
        self.technician = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.other = User.objects.create_user(email='b@example.com', password='p', name='B')

    def test_import_outgoing_creates_service_calls(self):
        invoice = InvoiceService.import_outgoing(
            technician=self.technician, upload=build_invoice_pdf(),
        )
        self.assertEqual(invoice.number, '22656')
        self.assertEqual(invoice.source_calls.count(), 3)

    def test_import_incoming_creates_invoice_and_labels(self):
        invoice = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(),
        )
        self.assertEqual(invoice.number, '22823')
        self.assertEqual(invoice.return_code, '23734')
        self.assertEqual(invoice.volumes, 1)
        self.assertEqual(invoice.items.count(), 3)

    def test_isolation_by_technician(self):
        InvoiceService.import_outgoing(
            technician=self.technician, upload=build_invoice_pdf(),
        )
        self.assertEqual(InvoiceService.list_by_technician(self.other).count(), 0)
        self.assertEqual(InvoiceService.list_by_technician(self.technician).count(), 1)

    def test_reassociate_matches_pending(self):
        from apps.services.models import ServiceCall
        InvoiceService.import_outgoing(
            technician=self.technician, upload=build_invoice_pdf(),
        )
        incoming = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(retorno_refs='99999'),
        )
        incoming.return_refs = '22656'
        incoming.save(update_fields=['return_refs'])
        associated = InvoiceService.reassociate(incoming.pk, self.technician)
        self.assertEqual(associated, 3)
        self.assertEqual(
            ServiceCall.objects.filter(destination_invoice=incoming).count(), 3,
        )

    def test_reassociate_multiple_calls_same_nf(self):
        from apps.services.models import ServiceCall
        incoming = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(retorno_refs='99999'),
        )
        incoming.return_refs = '22656'
        incoming.save(update_fields=['return_refs'])
        for _ in range(3):
            ServiceCall.objects.create(
                technician=self.technician, part_name='PEÇA TESTE',
                quantity=1, status='new', source_invoice_number='22656',
            )
        associated = InvoiceService.reassociate(incoming.pk, self.technician)
        self.assertEqual(associated, 3)
        self.assertEqual(
            ServiceCall.objects.filter(destination_invoice=incoming).count(), 3,
        )

    def test_reassociate_all_pending_matched(self):
        from apps.services.models import ServiceCall
        incoming = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(retorno_refs='99999'),
        )
        incoming.return_refs = '22656'
        incoming.save(update_fields=['return_refs'])
        for _ in range(5):
            ServiceCall.objects.create(
                technician=self.technician, part_name='PEÇA TESTE',
                quantity=1, status='new', source_invoice_number='22656',
            )
        associated = InvoiceService.reassociate(incoming.pk, self.technician)
        self.assertEqual(associated, 5)

    def test_reassociate_multiple_refs(self):
        from apps.services.models import ServiceCall
        incoming = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(retorno_refs='99999'),
        )
        incoming.return_refs = '22656 / 22700'
        incoming.save(update_fields=['return_refs'])
        ServiceCall.objects.create(
            technician=self.technician, part_name='PEÇA A',
            quantity=1, status='new', source_invoice_number='22656',
        )
        ServiceCall.objects.create(
            technician=self.technician, part_name='PEÇA B',
            quantity=1, status='new', source_invoice_number='22700',
        )
        ServiceCall.objects.create(
            technician=self.technician, part_name='PEÇA C',
            quantity=1, status='new', source_invoice_number='22656',
        )
        associated = InvoiceService.reassociate(incoming.pk, self.technician)
        self.assertEqual(associated, 3)

    def test_reassociate_during_import(self):
        from apps.services.models import ServiceCall
        InvoiceService.import_outgoing(
            technician=self.technician, upload=build_invoice_pdf(),
        )
        incoming = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(),
        )
        self.assertEqual(
            ServiceCall.objects.filter(destination_invoice=incoming).count(), 3,
        )

    def test_reassociate_skips_already_matched(self):
        from apps.services.models import ServiceCall
        incoming = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(retorno_refs='99999'),
        )
        incoming.return_refs = '22656'
        incoming.save(update_fields=['return_refs'])
        ServiceCall.objects.create(
            technician=self.technician, part_name='PEÇA TESTE',
            quantity=1, status='attended', source_invoice_number='22656',
            destination_invoice=incoming,
        )
        associated = InvoiceService.reassociate(incoming.pk, self.technician)
        self.assertEqual(associated, 0)

    def test_reassociate_empty_return_refs(self):
        incoming = InvoiceService.import_incoming(
            technician=self.technician, upload=build_incoming_pdf(retorno_refs='99999'),
        )
        incoming.return_refs = ''
        incoming.save(update_fields=['return_refs'])
        associated = InvoiceService.reassociate(incoming.pk, self.technician)
        self.assertEqual(associated, 0)