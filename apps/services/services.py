"""Casos de uso do módulo de Atendimento (RF-01, RF-03).

Isolamento por técnico (RN-04): todo método recebe o técnico logado.
"""
from django.utils import timezone

from apps.services.repositories import ServiceCallRepository


class ServiceCallService:
    @staticmethod
    def list_by_technician(technician):
        """Atendimentos ativos do técnico (RF-03 — histórico)."""
        return ServiceCallRepository.for_technician(technician).order_by('-date', '-created_at')

    @staticmethod
    def get_for_technician(pk, technician):
        return ServiceCallRepository.get_for_technician(pk, technician)

    @staticmethod
    def create(technician, *, ticket_number, serial_number='', part_name, defect, date=None):
        """Data automática PT-BR (default = hoje local)."""
        if date is None:
            date = timezone.localdate()
        return ServiceCallRepository.create(
            technician=technician,
            ticket_number=ticket_number,
            serial_number=serial_number,
            part_name=part_name,
            defect=defect,
            date=date,
        )

    @staticmethod
    def update(call, *, ticket_number, serial_number='', part_name, defect, date):
        return ServiceCallRepository.update(
            call,
            ticket_number=ticket_number,
            serial_number=serial_number,
            part_name=part_name,
            defect=defect,
            date=date,
        )

    @staticmethod
    def archive(call):
        call.archive()
