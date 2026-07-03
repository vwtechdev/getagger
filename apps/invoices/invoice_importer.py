"""Importação de Nota Fiscal (PDF) — pdfplumber.

Regras (PRD):
- RN-13: extração FIXA de rótulos do DANFE:
    * Número da NF-e: campo "NÚMERO" do cabeçalho do DANFE
      (bloco "NÚMERO <n> ... SÉRIE ... DANFE").
    * Código de Devolução (Romaneio): "Observacao: Codigo Devolucao: XXXX".
  Não inferir/variar rótulos.
- Tabela "DADOS DOS PRODUTOS / SERVIÇOS": extrair SOMENTE CÓD. PROD e DESCRIÇÃO.
- Sem OCR quando o PDF possuir texto pesquisável.
- RN-05: NENHUMA comparação/matching com nome da peça.
- O PDF NÃO é persistido — apenas extraído o conteúdo.
"""
import re

import pdfplumber

# Rótulos fixos (RN-13) — jamais variar.
# Número da NF-e: campo "NÚMERO" do cabeçalho do DANFE, seguido de SÉRIE e DANFE.
NUMBER_RE = re.compile(
    r'NÚMERO\s+(\d+)(?:\s+\d+)?\s*\n\s*\d*\s*\n?\s*SÉRIE\s*\n?\s*DANFE',
    re.IGNORECASE,
)
# Código de Devolução (Romaneio): rótulo fixo no campo de observações.
RETURN_CODE_RE = re.compile(
    r'Observacao:\s*Codigo Devolucao:\s*([^\s\n]+)', re.IGNORECASE
)

SECTION_HEADER = 'DADOS DOS PRODUTOS / SERVIÇOS'
SECTION_END = 'DADOS ADICIONAIS'


class InvoiceImportError(Exception):
    """Falha controlada na importação (ex.: rótulos RN-13 ausentes)."""


def _group_lines(words, tol=3):
    """Agrupa palavras em linhas pelo atributo ``top`` (tolerância em pontos)."""
    lines = []
    cur = []
    cur_top = None
    for w in sorted(words, key=lambda x: (x['top'], x['x0'])):
        if cur_top is None or abs(w['top'] - cur_top) <= tol:
            cur.append(w)
            cur_top = w['top'] if cur_top is None else cur_top
        else:
            lines.append(cur)
            cur = [w]
            cur_top = w['top']
    if cur:
        lines.append(cur)
    return lines


def _header_columns(line):
    """Identifica as posições x das colunas CÓD. PROD, DESCRIÇÃO e NCM."""
    code_x = desc_x = ncm_x = None
    for w in line:
        t = w['text'].upper()
        if t.startswith('CÓD') or t.startswith('COD') or t == 'CÓDIGO':
            code_x = w['x0']
        if 'DESCRI' in t and desc_x is None:
            desc_x = w['x0']
        if t.startswith('NCM') and ncm_x is None:
            ncm_x = w['x0']
    return code_x, desc_x, ncm_x


def _extract_items(pdf):
    """Localiza a seção 'DADOS DOS PRODUTOS / SERVIÇOS' e extrai os itens.

    Estratégia: localiza o cabeçalho da seção por posição (y), recorta a
    região até a próxima seção ('DADOS ADICIONAIS') e alinha as palavras
    pelas colunas do cabeçalho (CÓD. PROD / DESCRIÇÃO / NCM) — robusto a
    números dentro da descrição da peça.
    """
    items = []
    seen = set()

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

        crop = page.crop((0, y0, page.width, y1))
        words = crop.extract_words()
        if not words:
            continue

        lines = _group_lines(words)

        code_x = desc_x = ncm_x = None
        for ln in lines:
            joined = ' '.join(w['text'] for w in ln).upper()
            if ('CÓD.' in joined or 'COD.' in joined or 'CÓDIGO' in joined) and 'DESCRI' in joined:
                code_x, desc_x, ncm_x = _header_columns(ln)
                break

        if code_x is None or desc_x is None:
            continue
        if ncm_x is None:
            ncm_x = page.width

        for ln in lines:
            joined = ' '.join(w['text'] for w in ln).upper()
            if 'DESCRI' in joined or 'CÓD.' in joined or 'DADOS' in joined:
                continue
            ln_sorted = sorted(ln, key=lambda x: x['x0'])
            if not ln_sorted or not re.match(r'^\d+$', ln_sorted[0]['text']):
                continue
            code = ln_sorted[0]['text']
            # Descrição = palavras após o código até o NCM (8 dígitos, fixo no DANFE).
            desc_ws = []
            for w in ln_sorted[1:]:
                if re.match(r'^\d{8}$', w['text']):
                    break
                desc_ws.append(w)
            desc = ' '.join(w['text'] for w in desc_ws).strip()
            if not code or not desc:
                continue
            key = (code, desc)
            if key in seen:
                continue
            seen.add(key)
            items.append({'product_code': code, 'description': desc})
    return items


def extract_invoice(pdf_file):
    """Extrai number, return_code (RN-13) e itens da tabela de produtos.

    ``pdf_file``: path ou file-like (não é persistido).
    Retorna dict: {number, return_code, items: [{product_code, description}]}.
    Levanta InvoiceImportError se os rótulos fixos (RN-13) não forem encontrados.
    """
    full_text = ''
    with pdfplumber.open(pdf_file) as pdf:
        items = _extract_items(pdf)
        for page in pdf.pages:
            full_text += page.extract_text() or ''
            full_text += '\n'

    number_match = NUMBER_RE.search(full_text)
    return_code_match = RETURN_CODE_RE.search(full_text)

    if not number_match:
        raise InvoiceImportError(
            'Campo "NÚMERO" do cabeçalho do DANFE não encontrado no PDF (RN-13).'
        )
    if not return_code_match:
        raise InvoiceImportError(
            'Rótulo fixo "Observacao: Codigo Devolucao:" não encontrado (RN-13).'
        )

    return {
        'number': number_match.group(1),
        'return_code': return_code_match.group(1),
        'items': items,
    }
