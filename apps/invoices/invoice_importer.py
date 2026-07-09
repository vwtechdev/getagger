"""Importação de Nota Fiscal (PDF) — pdfplumber.

Suporta dois tipos de NF:
  - outgoing (NF de saída): extrai NÚMERO + itens (CÓD. PROD, DESCRIÇÃO, QUANTIDADE)
  - incoming (NF de entrada): extrai NÚMERO + TRANSPORTADOR/VOLUME (quantidade)
    + itens (CÓD. PROD, DESCRIÇÃO, QUANTIDADE) + Codigo Devolucao + RETORNO REF. NF
"""
import re

import pdfplumber

NUMBER_RE = re.compile(
    r'NÚMERO\s+(\d+)(?:\s+\d+)?\s*\n\s*\d*\s*\n?\s*SÉRIE\s*\n?\s*DANFE',
    re.IGNORECASE,
)
RETURN_CODE_RE = re.compile(
    r'Observacao:\s*Codigo Devolucao:\s*([^\s\n]+)', re.IGNORECASE
)
RETORNO_REF_RE = re.compile(
    r'RETORNO\s*REF\.{0,2}\s*NF\.{0,3}:?\s*([\d\s/\-]+)', re.IGNORECASE
)
TRANSPORTADOR_QTD_RE = re.compile(
    r'TRANSPORTADOR\s*/\s*VOLUME.*?QUANTIDADE\s*\n?\s*(\d+)', re.IGNORECASE | re.DOTALL
)
# Fallback: extrair QUANTIDADE da row da tabela TRANSPORTADOR
TRANSPORTADOR_ROW_RE = re.compile(
    r'^\s*(\d+)\s+(?:Volume|Caixa|Volume\(s\)|Caixa\(s\)|Pacote|Unidade)', re.IGNORECASE
)

SECTION_HEADER = 'DADOS DOS PRODUTOS / SERVIÇOS'
SECTION_END = 'DADOS ADICIONAIS'


class InvoiceImportError(Exception):
    pass


def _parse_br_number(text):
    """Converte número com formato brasileiro (ex.: '2,0000') para int."""
    if not text:
        return None
    cleaned = text.strip().replace('.', '').replace(',', '.')
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def _extract_items_with_qty(pdf):
    """Extrai itens da tabela 'DADOS DOS PRODUTOS / SERVIÇOS' usando extract_tables.

    Retorna lista de dicts: {product_code, description, quantity}
    """
    items = []
    for page in pdf.pages:
        starts = page.search(SECTION_HEADER)
        if not starts:
            continue
        y0 = max(r['bottom'] for r in starts)
        ends = page.search(SECTION_END)
        y1 = page.height
        if ends:
            after = [r['top'] for r in ends if r['top'] > y0]
            if after:
                y1 = min(after)

        tables = page.find_tables()
        prod_table = None
        for table in tables:
            rows = table.extract()
            if not rows:
                continue
            for row in rows:
                if row[0] and 'CÓD. PROD' in str(row[0]).upper():
                    prod_table = table
                    break
            if prod_table:
                break

        if not prod_table:
            continue

        header_idx = None
        for i, row in enumerate(rows):
            if row[0] and 'CÓD. PROD' in str(row[0]).upper():
                header_idx = i
                break
        if header_idx is None:
            continue

        qty_col = None
        header = rows[header_idx]
        for i, cell in enumerate(header):
            if cell and 'QUANTIDADE' in str(cell).upper():
                qty_col = i
                break

        for row in rows[header_idx + 1:]:
            if not row or not row[0]:
                continue
            code = str(row[0]).strip()
            if not code or not code.isdigit():
                continue
            desc = str(row[1]).strip() if len(row) > 1 and row[1] else ''
            if not desc or len(desc) < 3:
                continue
            desc = desc.split('\n')[0].strip()
            quantity = 1
            if qty_col is not None and len(row) > qty_col and row[qty_col]:
                parsed = _parse_br_number(str(row[qty_col]).strip())
                if parsed is not None and 1 <= parsed <= 99999:
                    quantity = parsed
            # Se mesmo código e descrição aparecem de novo, mantém como item separado
            items.append({'product_code': code, 'description': desc, 'quantity': quantity})

        if items:
            break

    return items


def _extract_full_text(pdf_file):
    full_text = ''
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() or ''
            full_text += '\n'
    return full_text


def extract_outgoing(pdf_file):
    """Extrai dados de NF de saída: number + itens (com quantidade).

    NÃO extrai return_code nem volumes.
    """
    items = []
    number = None
    full_text = ''
    with pdfplumber.open(pdf_file) as pdf:
        items = _extract_items_with_qty(pdf)
        for page in pdf.pages:
            full_text += page.extract_text() or ''
            full_text += '\n'
    number_match = NUMBER_RE.search(full_text)
    if not number_match:
        raise InvoiceImportError('Campo "NÚMERO" do cabeçalho do DANFE não encontrado no PDF.')
    number = number_match.group(1)
    return {
        'number': number,
        'items': items,
    }


def extract_incoming(pdf_file):
    """Extrai dados de NF de entrada: NÚMERO, volumes, itens (com qtd),
    return_code, e RETORNO REF NF list.
    """
    items = []
    number = None
    return_code = None
    volumes = 1
    retorno_refs = []

    with pdfplumber.open(pdf_file) as pdf:
        items = _extract_items_with_qty(pdf)
        full_text = ''
        for page in pdf.pages:
            full_text += page.extract_text() or ''
            full_text += '\n'

    number_match = NUMBER_RE.search(full_text)
    if not number_match:
        raise InvoiceImportError('Campo "NÚMERO" do cabeçalho do DANFE não encontrado no PDF.')
    number = number_match.group(1)

    return_code_match = RETURN_CODE_RE.search(full_text)
    if not return_code_match:
        raise InvoiceImportError('Rótulo fixo "Observacao: Codigo Devolucao:" não encontrado (RN-13).')
    return_code = return_code_match.group(1)

    transportador_match = TRANSPORTADOR_QTD_RE.search(full_text)
    if transportador_match:
        try:
            volumes = int(transportador_match.group(1))
        except (ValueError, TypeError):
            volumes = 1

    if volumes == 1:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.find_tables()
                for table in tables:
                    rows = table.extract()
                    for i, row in enumerate(rows):
                        if not row or not row[0]:
                            continue
                        cell = str(row[0]).upper()
                        if 'QUANTIDADE' in cell:
                            if i + 1 < len(rows) and rows[i + 1] and rows[i + 1][0]:
                                val = _parse_br_number(str(rows[i + 1][0]).strip().split()[0])
                                if val and 1 <= val <= 1000:
                                    volumes = val
                                    break
                    if volumes > 1:
                        break
                if volumes > 1:
                    break

    retorno_match = RETORNO_REF_RE.search(full_text)
    if retorno_match:
        raw = retorno_match.group(1)
        refs = re.split(r'[/\s]+', raw.strip())
        retorno_refs = [r.strip() for r in refs if r.strip().isdigit()]

    return {
        'number': number,
        'return_code': return_code,
        'volumes': volumes,
        'items': items,
        'retorno_refs': retorno_refs,
    }


extract_invoice = extract_incoming