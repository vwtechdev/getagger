"""Casos de uso do módulo de Nota Fiscal (RF-04).

Isolamento por técnico (RN-04). O PDF não é persistido — apenas extraído.
"""
from django.db import models, transaction
from django.db.models import Q

from apps.invoices import invoice_importer
from apps.invoices.models import InvoiceItem
from apps.invoices.repositories import InvoiceRepository


class InvoiceService:
    @staticmethod
    def list_by_technician(technician):
        return InvoiceRepository.for_technician(technician)

    @staticmethod
    def get_for_technician(pk, technician):
        return InvoiceRepository.get_for_technician(pk, technician)

    @staticmethod
    @transaction.atomic
    def import_outgoing(technician, *, upload):
        """Importa NF de saída: extrai itens, cria Invoice e ServiceCalls."""
        from apps.services.models import ServiceCall

        upload.seek(0)
        data = invoice_importer.extract_outgoing(upload)

        invoice = InvoiceRepository.create(
            technician=technician, type='outgoing', number=data['number'],
        )
        for item in data['items']:
            desc = item['description'].upper()
            InvoiceItem.objects.create(
                invoice=invoice,
                product_code=item['product_code'],
                description=desc,
                quantity=item.get('quantity', 1),
            )
            for _ in range(item['quantity']):
                ServiceCall.objects.create(
                    technician=technician,
                    part_name=desc,
                    quantity=1,
                    status='new',
                    source_invoice=invoice,
                )
        return invoice

    @staticmethod
    @transaction.atomic
    def import_incoming(technician, *, upload):
        """Importa NF de entrada: extrai itens, associa via RETORNO REF NF, gera etiquetas."""
        from apps.labels.services import LabelService
        from apps.services.models import ServiceCall

        upload.seek(0)
        data = invoice_importer.extract_incoming(upload)

        invoice = InvoiceRepository.create(
            technician=technician, type='incoming', number=data['number'],
            return_code=data['return_code'], volumes=data['volumes'],
        )
        ref_numbers = data.get('retorno_refs', [])
        if ref_numbers:
            invoice.return_refs = ' / '.join(ref_numbers)
            invoice.save(update_fields=['return_refs'])
        for item in data['items']:
            desc = item['description'].upper()
            InvoiceItem.objects.create(
                invoice=invoice,
                product_code=item['product_code'],
                description=desc,
                quantity=item.get('quantity', 1),
            )

        # Associação automática via RETORNO REF NF
        if ref_numbers:
            calls = ServiceCall.objects.filter(
                technician=technician,
                destination_invoice__isnull=True,
            ).filter(
                Q(source_invoice__number__in=ref_numbers) | Q(source_invoice_number__in=ref_numbers)
            )
            for call in calls:
                call.destination_invoice = invoice
                call.status = 'attended'
                call.part_name = call.part_name.upper()
                call.save(update_fields=['destination_invoice', 'status', 'part_name'])

        # Só gera etiquetas se houver peças associadas
        if invoice.destination_calls.exists():
            LabelService.ensure_invoice_labels(invoice)

        return invoice

    @staticmethod
    @transaction.atomic
    def reassociate(invoice_id, technician):
        """Re-associa ServiceCalls pendentes a uma NF de entrada usando return_refs."""
        from apps.services.models import ServiceCall

        invoice = InvoiceRepository.get_for_technician(invoice_id, technician)
        if not invoice.return_refs:
            return 0
        ref_numbers = [r.strip() for r in invoice.return_refs.split('/') if r.strip()]
        associated = 0
        calls = ServiceCall.objects.filter(
            technician=technician,
            destination_invoice__isnull=True,
        ).filter(
            Q(source_invoice__number__in=ref_numbers) | Q(source_invoice_number__in=ref_numbers)
        )
        for call in calls:
            call.destination_invoice = invoice
            call.status = 'attended'
            call.part_name = call.part_name.upper()
            call.save(update_fields=['destination_invoice', 'status', 'part_name'])
            associated += 1
        return associated

    @staticmethod
    @transaction.atomic
    def delete(pk, technician):
        from apps.labels.models import InvoiceLabel, PartLabel
        from apps.services.models import ServiceCall
        invoice = InvoiceRepository.get_for_technician(pk, technician)
        InvoiceLabel.objects.filter(invoice=invoice).delete()
        InvoiceItem.objects.filter(invoice=invoice).delete()
        if invoice.type == 'outgoing':
            calls = ServiceCall.objects.filter(source_invoice=invoice)
        else:
            calls = ServiceCall.objects.filter(destination_invoice=invoice)
        PartLabel.objects.filter(service_call__in=calls).delete()
        for call in calls:
            call.archive()
        invoice.archive()