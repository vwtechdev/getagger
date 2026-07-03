from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.services.forms import ServiceCallForm
from apps.services.services import ServiceCallService


@login_required
def service_call_list(request):
    calls = ServiceCallService.list_by_technician(request.user)
    return render(request, 'services/service_call_list.html', {'calls': calls})


@login_required
def service_call_new(request):
    form = ServiceCallForm(request.POST or None)
    if form.is_valid():
        call = ServiceCallService.create(
            technician=request.user,
            ticket_number=form.cleaned_data['ticket_number'],
            part_name=form.cleaned_data['part_name'],
            defect=form.cleaned_data['defect'],
            date=form.cleaned_data['date'],
        )
        messages.success(request, f'Atendimento {call.ticket_number} criado.')
        return redirect('services:service_call_detail', pk=call.pk)
    return render(request, 'services/service_call_form.html', {'form': form, 'creating': True})


@login_required
def service_call_edit(request, pk):
    call = ServiceCallService.get_for_technician(pk, request.user)
    form = ServiceCallForm(request.POST or None, instance=call)
    if form.is_valid():
        ServiceCallService.update(
            call,
            ticket_number=form.cleaned_data['ticket_number'],
            part_name=form.cleaned_data['part_name'],
            defect=form.cleaned_data['defect'],
            date=form.cleaned_data['date'],
        )
        messages.success(request, 'Atendimento atualizado.')
        return redirect('services:service_call_detail', pk=call.pk)
    return render(request, 'services/service_call_form.html', {'form': form, 'creating': False})


@login_required
def service_call_detail(request, pk):
    call = ServiceCallService.get_for_technician(pk, request.user)
    return render(request, 'services/service_call_detail.html', {'call': call})
