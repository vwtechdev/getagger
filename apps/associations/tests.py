from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.associations.services import AssociationService
from apps.invoices.tests import build_invoice_pdf
from apps.invoices.services import InvoiceService
from apps.labels.services import LabelService
from apps.services.services import ServiceCallService

User = get_user_model()


class AssociationServiceTest(TestCase):
    def setUp(self):
        self.tech_a = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.tech_b = User.objects.create_user(email='b@example.com', password='p', name='B')
        self.call1 = ServiceCallService.create(
            technician=self.tech_a, ticket_number='1', part_name='SSD', defect='x')
        self.call2 = ServiceCallService.create(
            technician=self.tech_a, ticket_number='2', part_name='HD', defect='y')
        self.invoice = InvoiceService.import_invoice(
            technician=self.tech_a, upload=build_invoice_pdf(), volumes=1)
        self.items = list(self.invoice.items.all())

    def test_create_manual_association(self):
        """RN-06: vínculo criado manualmente com ids explícitos."""
        assoc = AssociationService.create(
            item_id=self.items[0].pk, service_call_id=self.call1.pk, technician=self.tech_a)
        self.assertEqual(assoc.service_call_id, self.call1.pk)
        self.assertEqual(assoc.invoice_item_id, self.items[0].pk)

    def test_create_archives_service_call(self):
        """Após associar, o ServiceCall é arquivado (não aparece na lista)."""
        AssociationService.create(
            item_id=self.items[0].pk, service_call_id=self.call1.pk, technician=self.tech_a)
        self.call1.refresh_from_db()
        self.assertTrue(self.call1.is_archived)
        # Não aparece na lista de peças disponíveis nem na lista principal.
        self.assertNotIn(self.call1, AssociationService.available_service_calls(self.tech_a, self.invoice))
        self.assertNotIn(self.call1, ServiceCallService.list_by_technician(self.tech_a))

    def test_one_to_one_enforcement(self):
        """Um service_call arquivado não pode ser reassociado (1:1)."""
        AssociationService.create(
            item_id=self.items[0].pk, service_call_id=self.call1.pk, technician=self.tech_a)
        with self.assertRaises(Exception):
            AssociationService.create(
                item_id=self.items[1].pk, service_call_id=self.call1.pk, technician=self.tech_a)

    def test_undo_releases_item_and_call(self):
        """Desfazer desarquiva o ServiceCall ( volta a ficar disponível)."""
        AssociationService.create(
            item_id=self.items[0].pk, service_call_id=self.call1.pk, technician=self.tech_a)
        assoc = AssociationService.list_for_invoice(self.invoice).first()
        AssociationService.undo(assoc.pk, self.tech_a)
        self.call1.refresh_from_db()
        self.assertFalse(self.call1.is_archived)
        self.assertEqual(AssociationService.list_for_invoice(self.invoice).count(), 0)
        self.assertEqual(AssociationService.pending_items(self.invoice).count(), 3)
        self.assertIn(self.call1, AssociationService.available_service_calls(self.tech_a, self.invoice))

    def test_counters(self):
        AssociationService.create(
            item_id=self.items[0].pk, service_call_id=self.call1.pk, technician=self.tech_a)
        c = AssociationService.counters(self.invoice, self.tech_a)
        self.assertEqual(c['total_items'], 3)
        self.assertEqual(c['associated'], 1)
        self.assertEqual(c['pending'], 2)
        self.assertEqual(c['remaining'], 1)  # call2 ainda livre

    def test_isolation_blocks_other_technician(self):
        """RN-04: técnico B não associa item/call do técnico A."""
        with self.assertRaises(Exception):
            AssociationService.create(
                item_id=self.items[0].pk, service_call_id=self.call1.pk, technician=self.tech_b)
        with self.assertRaises(Exception):
            AssociationService.create(
                item_id=self.items[0].pk, service_call_id='00000000-0000-0000-0000-000000000000',
                technician=self.tech_b)

    def test_no_auto_matching_api(self):
        """RN-05/RN-06: nenhum método de auto-match/fuzzy/infer exposto."""
        forbidden = ('auto_match', 'fuzzy', 'infer', 'suggest', 'deduce')
        for name in dir(AssociationService):
            self.assertFalse(any(f in name.lower() for f in forbidden),
                             f'Método suspeito de auto-match: {name}')
        # create exige ids explícitos (não deduz nada).
        with self.assertRaises(TypeError):
            AssociationService.create(technician=self.tech_a)


class FullFlowIntegrationTest(TestCase):
    """RF-04..RF-08 + RN-04: fluxo completo e isolamento entre técnicos."""

    def setUp(self):
        self.tech_a = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.tech_b = User.objects.create_user(email='b@example.com', password='p', name='B')

    def test_full_flow_and_isolation(self):
        calls = [
            ServiceCallService.create(
                technician=self.tech_a, ticket_number='1', part_name='SSD', defect='x'),
            ServiceCallService.create(
                technician=self.tech_a, ticket_number='2', part_name='HD', defect='y'),
        ]
        invoice = InvoiceService.import_invoice(
            technician=self.tech_a, upload=build_invoice_pdf(), volumes=2)
        items = list(invoice.items.all())

        # Associação manual (RN-06).
        AssociationService.create(
            item_id=items[0].pk, service_call_id=calls[0].pk, technician=self.tech_a)
        AssociationService.create(
            item_id=items[1].pk, service_call_id=calls[1].pk, technician=self.tech_a)

        # Etiquetas: peças (1 por peça) e romaneio (1 por volume) — PDFs separados.
        part_pdf = LabelService.generate_part_labels_pdf(invoice)
        romaneio_pdf = LabelService.generate_invoice_labels_pdf(invoice)
        self.assertGreaterEqual(len(part_pdf), 200)
        self.assertGreaterEqual(len(romaneio_pdf), 200)

        # RN-04: técnico B não enxerga nada do técnico A.
        self.assertEqual(ServiceCallService.list_by_technician(self.tech_b).count(), 0)
        self.assertEqual(InvoiceService.list_by_technician(self.tech_b).count(), 0)
        self.assertEqual(AssociationService.list_for_invoice(invoice).filter(
            service_call__technician=self.tech_b).count(), 0)
