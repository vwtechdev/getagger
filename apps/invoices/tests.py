import io
from datetime import date

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
    """Gera uma NF-PDF sintética em memória (rótulos fixos RN-13 + tabela)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    flow = []
    if include_labels:
        # Cabeçalho DANFE: "NÚMERO <n> <série> SÉRIE DANFE".
        flow.append(Paragraph(f'NÚMERO {number}', styles['Normal']))
        flow.append(Paragraph('1', styles['Normal']))
        flow.append(Paragraph('SÉRIE', styles['Normal']))
        flow.append(Paragraph('DANFE', styles['Normal']))
        flow.append(Paragraph(f'Observacao: Codigo Devolucao: {return_code}', styles['Normal']))
        flow.append(Spacer(1, 12))
    flow.append(Paragraph('DADOS DOS PRODUTOS / SERVIÇOS', styles['Heading2']))
    flow.append(Spacer(1, 6))
    table = Table([
        ['CÓD. PROD', 'DESCRIÇÃO DOS PRODUTOS / SERVIÇOS', 'NCM', 'CFOP'],
        ['0001', 'SSD NVMe 1TB', '84717000', '5405'],
        ['0002', 'Memória DDR4 16GB', '84733000', '5405'],
        ['0003', 'Fonte ATX 650W', '85044000', '5405'],
    ])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    flow.append(table)
    doc.build(flow)
    buf.seek(0)
    return buf


class InvoiceImporterTest(TestCase):
    def test_extract_fixed_labels_and_items(self):
        """RN-13: rótulos fixos + tabela (somente CÓD. PROD e DESCRIÇÃO)."""
        data = invoice_importer.extract_invoice(build_invoice_pdf())
        self.assertEqual(data['number'], '22656')
        self.assertEqual(data['return_code'], '23788')
        codes = [i['product_code'] for i in data['items']]
        descs = [i['description'] for i in data['items']]
        self.assertEqual(codes, ['0001', '0002', '0003'])
        self.assertIn('SSD NVMe 1TB', descs)
        # Ignora colunas extras (NCM/CFOP).
        self.assertEqual(set(data['items'][0].keys()), {'product_code', 'description'})

    def test_missing_labels_raises(self):
        """RN-13: sem os rótulos fixos -> InvoiceImportError."""
        buf = build_invoice_pdf(include_labels=False)
        with self.assertRaises(invoice_importer.InvoiceImportError):
            invoice_importer.extract_invoice(buf)


class InvoiceServiceTest(TestCase):
    def setUp(self):
        self.technician = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.other = User.objects.create_user(email='b@example.com', password='p', name='B')

    def test_import_creates_invoice_items_and_romaneio(self):
        """RF-04/RF-08: importa NF, cria itens e N etiquetas romaneio (1 por volume)."""
        invoice = InvoiceService.import_invoice(
            technician=self.technician,
            upload=build_invoice_pdf(),
            volumes=3,
        )
        self.assertEqual(invoice.number, '22656')
        self.assertEqual(invoice.return_code, '23788')
        self.assertEqual(invoice.volumes, 3)
        self.assertEqual(invoice.items.count(), 3)
        # RN-11/RN-12: 1 InvoiceLabel por volume, 1..N.
        labels = list(InvoiceLabel.objects.filter(invoice=invoice).order_by('volume_index'))
        self.assertEqual([l.volume_index for l in labels], [1, 2, 3])

    def test_pdf_not_persisted(self):
        """O PDF nunca é persistido (Invoice sem FileField)."""
        invoice = InvoiceService.import_invoice(
            technician=self.technician, upload=build_invoice_pdf(), volumes=1
        )
        field_names = {f.name for f in Invoice._meta.get_fields()}
        self.assertNotIn('arquivo', field_names)
        self.assertFalse(InvoiceItem._meta.get_field('product_code').blank)

    def test_isolation_by_technician(self):
        """RN-04: técnico B não vê NFs do técnico A."""
        InvoiceService.import_invoice(
            technician=self.technician, upload=build_invoice_pdf(), volumes=1
        )
        self.assertEqual(InvoiceService.list_by_technician(self.other).count(), 0)
        self.assertEqual(InvoiceService.list_by_technician(self.technician).count(), 1)
