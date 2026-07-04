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
        # part_name='SSD' → auto-match com 'SSD NVMe 1TB' na NF
        # part_name='HD'  → sem match (nenhuma descrição da NF contém 'HD')
        self.call1 = ServiceCallService.create(
            technician=self.tech_a, ticket_number='1', part_name='SSD', defect='x')
        self.call2 = ServiceCallService.create(
            technician=self.tech_a, ticket_number='2', part_name='HD', defect='y')
        self.invoice = InvoiceService.import_invoice(
            technician=self.tech_a, upload=build_invoice_pdf(), volumes=1)
        self.items = list(self.invoice.items.all())

    def test_auto_match_matches_ssd(self):
        """auto_match associa call1 (SSD) ao item com descrição 'SSD NVMe 1TB'."""
        assocs = AssociationService.list_for_invoice(self.invoice)
        self.assertEqual(assocs.count(), 1)
        assoc = assocs.first()
        self.assertEqual(assoc.service_call_id, self.call1.pk)
        self.assertEqual(assoc.invoice_item.description, 'SSD NVMe 1TB')

    def test_auto_match_leaves_hd_pending(self):
        """call2 (HD) não tem match → item 'Memória DDR4 16GB' e 'Fonte ATX 650W' pendentes."""
        pending = AssociationService.pending_items(self.invoice)
        self.assertEqual(pending.count(), 2)

    def test_create_manual_association(self):
        """RN-06: vínculo criado manualmente com ids explícitos (item não auto-match)."""
        assoc = AssociationService.create(
            item_id=self.items[1].pk, service_call_id=self.call2.pk, technician=self.tech_a)
        self.assertEqual(assoc.service_call_id, self.call2.pk)
        self.assertEqual(assoc.invoice_item_id, self.items[1].pk)

    def test_create_archives_service_call(self):
        """Após associar manualmente, o ServiceCall é arquivado."""
        AssociationService.create(
            item_id=self.items[1].pk, service_call_id=self.call2.pk, technician=self.tech_a)
        self.call2.refresh_from_db()
        self.assertTrue(self.call2.is_archived)
        self.assertNotIn(self.call2, AssociationService.available_service_calls(self.tech_a, self.invoice))
        self.assertNotIn(self.call2, ServiceCallService.list_by_technician(self.tech_a))

    def test_one_to_one_enforcement(self):
        """Um service_call arquivado não pode ser reassociado (1:1)."""
        AssociationService.create(
            item_id=self.items[1].pk, service_call_id=self.call2.pk, technician=self.tech_a)
        with self.assertRaises(Exception):
            AssociationService.create(
                item_id=self.items[2].pk, service_call_id=self.call2.pk, technician=self.tech_a)

    def test_undo_releases_item_and_call(self):
        """Desfazer desarquiva o ServiceCall."""
        AssociationService.create(
            item_id=self.items[1].pk, service_call_id=self.call2.pk, technician=self.tech_a)
        assoc = AssociationService.list_for_invoice(self.invoice).get(
            service_call_id=self.call2.pk)
        AssociationService.undo(assoc.pk, self.tech_a)
        self.call2.refresh_from_db()
        self.assertFalse(self.call2.is_archived)
        self.assertEqual(AssociationService.pending_items(self.invoice).count(), 2)
        self.assertIn(self.call2, AssociationService.available_service_calls(self.tech_a, self.invoice))

    def test_counters(self):
        """Contadores refletem auto-match + associação manual."""
        # Após auto-match: 1 associado, 2 pendentes, 1 call disponível (call2)
        c = AssociationService.counters(self.invoice, self.tech_a)
        self.assertEqual(c['total_items'], 3)
        self.assertEqual(c['associated'], 1)
        self.assertEqual(c['pending'], 2)
        self.assertEqual(c['remaining'], 1)
        # Associa manualmente
        AssociationService.create(
            item_id=self.items[1].pk, service_call_id=self.call2.pk, technician=self.tech_a)
        c = AssociationService.counters(self.invoice, self.tech_a)
        self.assertEqual(c['associated'], 2)
        self.assertEqual(c['pending'], 1)
        self.assertEqual(c['remaining'], 0)

    def test_isolation_blocks_other_technician(self):
        """RN-04: técnico B não associa item/call do técnico A."""
        with self.assertRaises(Exception):
            AssociationService.create(
                item_id=self.items[1].pk, service_call_id=self.call2.pk, technician=self.tech_b)
        with self.assertRaises(Exception):
            AssociationService.create(
                item_id=self.items[1].pk, service_call_id='00000000-0000-0000-0000-000000000000',
                technician=self.tech_b)

    def test_auto_match_no_match_returns_zero(self):
        """auto_match com calls que não batem com descrições não associa nada."""
        tech = User.objects.create_user(email='c@example.com', password='p', name='C')
        call = ServiceCallService.create(
            technician=tech, ticket_number='99', part_name='Monitor', defect='z')
        inv = InvoiceService.import_invoice(
            technician=tech, upload=build_invoice_pdf(), volumes=1)
        # 'Monitor' não está em nenhuma descrição → 0 matches
        self.assertEqual(
            AssociationService.list_for_invoice(inv).count(), 0)


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

        # Após import: auto-match associou call1 (SSD) ao item 0 (SSD NVMe 1TB).
        # Associar manualmente call2 (HD) ao item 1 (Memória DDR4 16GB).
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
