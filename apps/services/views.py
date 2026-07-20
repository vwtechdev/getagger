import calendar

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.services.forms import ServiceCallForm
from apps.services.models import ServiceCall
from apps.services.services import ServiceCallService


def _month_range():
    today = timezone.localdate()
    return (
        today.replace(day=1).isoformat(),
        today.replace(day=calendar.monthrange(today.year, today.month)[1]).isoformat(),
    )

@login_required
def service_call_list(request):
    qs = ServiceCallService.list_by_technician(request.user)
    q = request.GET.get('q', '').strip()
    default_from, default_to = _month_range()
    date_from = request.GET['date_from'].strip() if 'date_from' in request.GET else default_from
    date_to = request.GET['date_to'].strip() if 'date_to' in request.GET else default_to
    if q:
        qs = qs.filter(
            Q(ticket_number__icontains=q)
            | Q(part_name__icontains=q)
            | Q(defect__icontains=q)
        )
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    return render(request, 'services/service_call_list.html', {
        'calls': qs, 'q': q, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def service_call_new(request):
    today = timezone.localdate()
    form = ServiceCallForm(request.POST or None, initial={'date': today}, technician=request.user)
    if form.is_valid():
        quantity = form.cleaned_data.get('quantity') or 1
        ticket = form.cleaned_data['ticket_number']
        serial = form.cleaned_data['serial_number']
        defect = form.cleaned_data['defect']
        status = 'attended' if (ticket or serial or defect) else 'new'
        kwargs = dict(
            technician=request.user,
            ticket_number=ticket,
            serial_number=serial,
            part_name=form.cleaned_data['part_name'].upper(),
            defect=defect,
            date=form.cleaned_data['date'],
            source_invoice_number=form.cleaned_data.get('source_invoice_number', ''),
            quantity=1,
            status=status,
        )
        for _ in range(quantity):
            call = ServiceCallService.create(**kwargs)
        messages.success(request, f'{quantity} peça(s) {call.part_name} criada(s).')
        return redirect('services:service_call_list')
    return render(request, 'services/service_call_form.html', {
        'form': form, 'creating': True, 'today': today.isoformat(),
    })


@login_required
def service_call_edit(request, pk):
    call = ServiceCallService.get_for_technician(pk, request.user)
@login_required
def service_call_edit(request, pk):
    call = ServiceCallService.get_for_technician(pk, request.user)
    form = ServiceCallForm(request.POST or None, instance=call, technician=request.user)
    if form.is_valid():
        ticket = form.cleaned_data['ticket_number']
        serial = form.cleaned_data['serial_number']
        part_name = form.cleaned_data['part_name']
        defect = form.cleaned_data['defect']
        date = form.cleaned_data['date']
        ServiceCallService.update(call, ticket_number=ticket, serial_number=serial, part_name=part_name, defect=defect, date=date)
        if call.status == 'new':
            call.status = 'attended'
            call.save(update_fields=['status'])
        messages.success(request, 'Peça com defeito atualizada.')
        return redirect('services:service_call_list')
    return render(request, 'services/service_call_form.html', {'form': form, 'creating': False})
@login_required
@require_POST
def service_call_delete(request, pk):
    try:
        call = ServiceCallService.get_for_technician(pk, request.user)
        ServiceCallService.archive(call)
        messages.success(request, 'Peça com defeito excluída.')
    except Exception as exc:
        messages.error(request, f'Erro ao excluir: {exc}')
    return redirect('services:service_call_list')