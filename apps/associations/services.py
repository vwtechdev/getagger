"""Casos de uso de Associação (RF-05). Suporta auto-match (RN-05) e manual (RN-06).

Auto-match usa substring + fuzzy ratio + normalização fonética (sem dependências).
Manual: usuário informa explicitamente item_id + service_call_id no drag & drop.
"""
import unicodedata
from difflib import SequenceMatcher

from apps.associations.repositories import AssociationRepository
from apps.invoices.models import InvoiceItem
from apps.invoices.repositories import InvoiceItemRepository
from apps.services.models import ServiceCall
from apps.services.repositories import ServiceCallRepository


class AssociationService:
    @staticmethod
    def list_for_invoice(invoice):
        return AssociationRepository.for_invoice(invoice)

    @staticmethod
    def pending_items(invoice):
        """Itens da NF ainda não associados (não usa part_name — RN-05)."""
        return InvoiceItemRepository.pending_for_invoice(invoice)

    @staticmethod
    def auto_match(invoice, technician):
        """Associa automaticamente itens pendentes a atendimentos compatíveis.

        Matching de 3 níveis (tudo normalizado: lowercase + sem acentos):
          1. Substring: part_name contido em description
          2. Fuzzy ratio ≥ 0.85 entre strings completas
          3. Fuzzy ratio ≥ 0.85 entre palavras individuais

        Retorna dict com matched e pending.
        """
        items = AssociationService.pending_items(invoice)
        calls = list(AssociationService.available_service_calls(technician, invoice))
        matched = 0
        for item in items:
            if not item.description:
                continue
            for call in calls:
                if call.part_name and _match(call.part_name, item.description):
                    AssociationService.create(
                        item_id=item.pk,
                        service_call_id=call.pk,
                        technician=technician,
                    )
                    matched += 1
                    calls = [c for c in calls if c.pk != call.pk]
                    break
        return {'matched': matched, 'pending': items.count() - matched}

    @staticmethod
    def available_service_calls(technician, invoice):
        """Atendimentos do técnico ainda não associados a item algum."""
        associated = AssociationRepository.for_invoice(invoice).values_list(
            'service_call_id', flat=True
        )
        return (
            ServiceCallRepository.for_technician(technician)
            .exclude(pk__in=list(associated))
            .order_by('-date', '-created_at')
        )

    @staticmethod
    def counters(invoice, technician):
        total_items = invoice.items.count()
        associated = AssociationRepository.for_invoice(invoice).count()
        pending = max(total_items - associated, 0)
        remaining = AssociationService.available_service_calls(
            technician, invoice
        ).count()
        return {
            'pending': pending,
            'associated': associated,
            'remaining': remaining,
            'total_items': total_items,
        }

    @staticmethod
    def create(*, item_id, service_call_id, technician):
        """Cria vínculo permanente (RN-06). Valida posse pelo técnico (RN-04).

        Após associar, arquiva o ServiceCall (não aparece mais na lista de
        peças disponíveis). O arquivamento é revertido ao desfazer.
        """
        service_call = ServiceCallRepository.get_for_technician(service_call_id, technician)
        item = _item_for_technician(item_id, technician)
        if AssociationRepository.for_invoice(item.invoice).filter(
            service_call=service_call
        ).exists():
            raise ValueError('Atendimento já associado a um item desta NF.')
        association = AssociationRepository.create(
            service_call=service_call, invoice_item=item
        )
        service_call.archive()
        return association

    @staticmethod
    def undo(association_id, technician):
        """Desfaz associação: remove vínculo e desarquiva o ServiceCall."""
        association = AssociationRepository.get_for_technician(association_id, technician)
        service_call = association.service_call
        AssociationRepository.delete(association)
        service_call.unarchive()


def _normalize(text):
    """Remove acentos, lowercase, strips."""
    nfkd = unicodedata.normalize('NFKD', str(text))
    return nfkd.encode('ascii', 'ignore').decode('ascii').lower().strip()


def _match(part_name, description):
    """Retorna True se part_name corresponde à descrição (3 níveis com guardrails)."""
    a = _normalize(part_name)
    b = _normalize(description)
    if not a or not b:
        return False
    # 1. Substring (rápido)
    if a in b:
        return True
    # 2. Fuzzy full — só se tamanhos forem compatíveis
    len_a, len_b = len(a), len(b)
    if max(len_a, len_b) / min(len_a, len_b, 1) <= 3:
        if SequenceMatcher(None, a, b).ratio() >= 0.85:
            return True
    # 3. Fuzzy por palavra — só até 50 comparações
    words_a = a.split()
    words_b = b.split()
    if len(words_a) * len(words_b) <= 50:
        for wa in words_a:
            for wb in words_b:
                if SequenceMatcher(None, wa, wb).ratio() >= 0.85:
                    return True
    return False


def _item_for_technician(item_id, technician):
    """Retorna InvoiceItem pertencente a uma NF do técnico (RN-04)."""
    return InvoiceItem.objects.select_related('invoice').get(
        pk=item_id, invoice__technician=technician
    )
