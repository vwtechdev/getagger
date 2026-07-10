from django.utils import timezone

from apps.services.repositories import ServiceCallRepository


class ServiceCallService:
    @staticmethod
    def list_by_technician(technician):
        return ServiceCallRepository.for_technician(technician).order_by('-date', '-created_at')

    @staticmethod
    def list_pending(technician):
        return ServiceCallRepository.for_technician(technician).filter(
            status='new'
        ).order_by('-date', '-created_at')

    @staticmethod
    def get_for_technician(pk, technician):
        return ServiceCallRepository.get_for_technician(pk, technician)

    @staticmethod
    def create(technician, *, ticket_number='', serial_number='', part_name, defect='', date=None, source_invoice_number='', quantity=1, status='new'):
        if date is None:
            date = timezone.localdate()
        return ServiceCallRepository.create(
            technician=technician,
            ticket_number=ticket_number,
            serial_number=serial_number,
            part_name=part_name,
            defect=defect,
            date=date,
            source_invoice_number=source_invoice_number,
            quantity=quantity,
            status=status,
        )

    @staticmethod
    def update(call, *, ticket_number='', serial_number='', part_name, defect='', date):
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