"""Geração de PDFs de etiquetas — ReportLab.

- Etiquetas de peça (RF-06): 1 por peça, com Código, Peça, Chamado, Data,
  Técnico, Defeito.
- Etiquetas romaneio (RF-08): 1 por volume, numeradas 1/N..N/N, com NF-e,
  Romaneio e Volume N/M. Saída em PDF SEPARADO (RN-11, RN-12).
"""
import io

from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _draw_label(c, title, lines):
    width, height = A6
    margin = 8 * mm
    c.setLineWidth(1.2)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width / 2, height - 18 * mm, title)

    y = height - 34 * mm
    for label, value in lines:
        c.setFont('Helvetica-Bold', 10)
        c.drawString(margin + 4 * mm, y, f'{label}:')
        c.setFont('Helvetica', 11)
        c.drawString(margin + 28 * mm, y, str(value))
        y -= 8 * mm


def generate_invoice_labels_pdf(invoice):
    """PDF (bytes) com N etiquetas romaneio (1 por volume). RN-11/RN-12."""
    total = max(int(invoice.volumes or 1), 1)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A6)
    for index in range(1, total + 1):
        lines = [
            ('NF-e', invoice.number),
            ('Romaneio', invoice.return_code),
            ('Volume', f'{index} de {total}'),
        ]
        _draw_label(c, 'ROMANEIO', lines)
        c.showPage()
    c.save()
    return buf.getvalue()


def generate_part_labels_pdf(part_labels):
    """PDF (bytes) com 1 etiqueta por peça. RF-06.

    ``part_labels``: queryset/iterável de PartLabel com associação carregada.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A6)
    if not part_labels:
        c.showPage()
        c.save()
        return buf.getvalue()

    for label in part_labels:
        assoc = label.association
        call = assoc.service_call
        item = assoc.invoice_item
        technician = call.technician.name or call.technician.email
        lines = [
            ('Código', item.product_code),
            ('Peça', call.part_name),
            ('Chamado', call.ticket_number),
            ('Data', call.date.strftime('%d/%m/%Y')),
            ('Técnico', technician),
            ('Defeito', call.defect),
        ]
        _draw_label(c, 'ETIQUETA DE DEFEITO', lines)
        c.showPage()
    c.save()
    return buf.getvalue()
