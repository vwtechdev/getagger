import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _cell_height(num_lines, font_size):
    title_h = (font_size + 3) * 1.3
    line_h = font_size * 1.35
    return 6 * mm + title_h + num_lines * line_h


def _draw_one(c, cx, cy, cw, ch, title, lines, font_size):
    pad = 2 * mm
    c.setLineWidth(1.2)
    c.rect(cx + pad, cy + pad, cw - 2 * pad, ch - 2 * pad)

    title_pt = font_size + 3
    c.setFont('Helvetica-Bold', title_pt)
    title_y = cy + ch - pad - title_pt * 1.3
    c.drawCentredString(cx + cw / 2, title_y, title)

    line_h = font_size * 1.35
    ly = title_y - line_h * 1.2
    for label, value in lines:
        c.setFont('Helvetica-Bold', font_size - 1)
        c.drawString(cx + pad + 2 * mm, ly, f'{label}:')
        c.setFont('Helvetica', font_size)
        max_val_w = cw - 2 * pad - 25 * mm - 2 * mm
        text = str(value) if value else '—'
        if c.stringWidth(text) > max_val_w:
            while text and c.stringWidth(text + '…') > max_val_w:
                text = text[:-1]
            text = text + '…'
        c.drawString(cx + pad + 25 * mm, ly, text)
        ly -= line_h


def _part_lines(label):
    call = label.service_call
    tech = call.technician.name or call.technician.email
    lines = [
        ('Peça', call.part_name),
        ('Chamado', call.ticket_number or '—'),
        ('Data', call.date.strftime('%d/%m/%Y')),
        ('Técnico', tech),
        ('Defeito', call.defect or '—'),
    ]
    if call.serial_number:
        lines.insert(2, ('N/S', call.serial_number))
    return lines


def _invoice_lines(invoice, index, total):
    return [
        ('NF-e', invoice.number),
        ('Romaneio', invoice.return_code),
        ('Volume', f'{index} de {total}'),
    ]


def generate_part_labels_pdf(part_labels, settings, title='ETIQUETA DE DEFEITO'):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    font_size = settings.font_size
    margin = float(settings.margin) * mm

    if not part_labels:
        c.showPage()
        c.save()
        return buf.getvalue()

    max_lines = max(len(_part_lines(pl)) for pl in part_labels)
    if settings.page_format == 'A4':
        _render_a4(c, part_labels, title, _part_lines, max_lines, font_size, margin)
    else:
        _render_thermal(c, part_labels, title, _part_lines, font_size)

    c.save()
    return buf.getvalue()


def generate_invoice_labels_pdf(invoice, settings):
    total = max(int(invoice.volumes or 1), 1)
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    font_size = settings.font_size
    margin = float(settings.margin) * mm

    class _Item:
        def __init__(self, invoice, index, total):
            self.invoice = invoice
            self.index = index
            self.total = total

    def _item_lines(item):
        return _invoice_lines(item.invoice, item.index, item.total)

    items = [_Item(invoice, i + 1, total) for i in range(total)]

    if settings.page_format == 'A4':
        _render_a4(c, items, 'ROMANEIO', _item_lines, 3, font_size, margin)
    else:
        _render_thermal(c, items, 'ROMANEIO', _item_lines, font_size)

    c.save()
    return buf.getvalue()


def _render_a4(c, objects, title, lines_fn, num_lines, font_size, margin):
    c.setPageSize(A4)
    usable_w = A4[0] - 2 * margin
    usable_h = A4[1] - 2 * margin
    cell_w = usable_w / 2
    cell_h = _cell_height(num_lines, font_size)
    rows = max(1, int(usable_h / cell_h))

    for idx, obj in enumerate(objects):
        pos = idx % (rows * 2)
        col = pos % 2
        row = pos // 2

        if pos == 0 and idx > 0:
            c.showPage()

        x = margin + col * cell_w
        cy = A4[1] - margin - (row + 1) * cell_h
        _draw_one(c, x, cy, cell_w, cell_h, title, lines_fn(obj), font_size)

    c.showPage()


def _render_thermal(c, objects, title, lines_fn, font_size):
    for obj in objects:
        lines = lines_fn(obj)
        cell_h = _cell_height(len(lines), font_size)
        page_h = cell_h + 2 * mm
        c.setPageSize((80 * mm, page_h))
        _draw_one(c, 0, 0, 80 * mm, page_h, title, lines, font_size)
        c.showPage()