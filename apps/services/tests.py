from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.services.services import ServiceCallService

User = get_user_model()


class ServiceCallServiceTest(TestCase):
    def setUp(self):
        self.tech_a = User.objects.create_user(email='a@example.com', password='p', name='A')
        self.tech_b = User.objects.create_user(email='b@example.com', password='p', name='B')

    def test_create_sets_auto_date(self):
        """Data automática PT-BR (default = hoje local)."""
        call = ServiceCallService.create(
            technician=self.tech_a, ticket_number='1', part_name='SSD', defect='x')
        self.assertEqual(call.date, timezone.localdate())
        self.assertEqual(call.technician, self.tech_a)

    def test_isolation_by_technician(self):
        """RN-04: técnico B não vê atendimentos do técnico A."""
        ServiceCallService.create(
            technician=self.tech_a, ticket_number='1', part_name='SSD', defect='x')
        self.assertEqual(ServiceCallService.list_by_technician(self.tech_a).count(), 1)
        self.assertEqual(ServiceCallService.list_by_technician(self.tech_b).count(), 0)

    def test_get_for_technician_blocks_other(self):
        call = ServiceCallService.create(
            technician=self.tech_a, ticket_number='1', part_name='SSD', defect='x')
        with self.assertRaises(Exception):
            ServiceCallService.get_for_technician(call.pk, self.tech_b)
