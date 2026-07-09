from apps.services.models import ServiceCall


class ServiceCallRepository:
    @staticmethod
    def for_technician(technician):
        return ServiceCall.objects.filter(technician=technician, archived_at__isnull=True)

    @staticmethod
    def get_for_technician(pk, technician):
        return ServiceCallRepository.for_technician(technician).get(pk=pk)

    @staticmethod
    def create(technician, *, ticket_number='', serial_number='', part_name, defect='', date=None, source_invoice_number='', quantity=1):
        return ServiceCall.objects.create(
            technician=technician,
            ticket_number=ticket_number,
            serial_number=serial_number,
            part_name=part_name,
            defect=defect,
            date=date,
            source_invoice_number=source_invoice_number,
            quantity=quantity,
        )

    @staticmethod
    def update(call, *, ticket_number='', serial_number='', part_name, defect='', date=None):
        call.ticket_number = ticket_number
        call.serial_number = serial_number
        call.part_name = part_name
        call.defect = defect
        if date is not None:
            call.date = date
        call.save()
        return call