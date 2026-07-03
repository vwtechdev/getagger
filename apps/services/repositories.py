"""Repository — acesso a dados isolado por técnico (RN-04)."""
from apps.services.models import ServiceCall


class ServiceCallRepository:
    @staticmethod
    def for_technician(technician):
        return ServiceCall.objects.filter(technician=technician, archived_at__isnull=True)

    @staticmethod
    def get_for_technician(pk, technician):
        return ServiceCallRepository.for_technician(technician).get(pk=pk)

    @staticmethod
    def create(technician, *, ticket_number, part_name, defect, date=None):
        return ServiceCall.objects.create(
            technician=technician,
            ticket_number=ticket_number,
            part_name=part_name,
            defect=defect,
            date=date,
        )

    @staticmethod
    def update(call, *, ticket_number, part_name, defect, date=None):
        call.ticket_number = ticket_number
        call.part_name = part_name
        call.defect = defect
        if date is not None:
            call.date = date
        call.save()
        return call
