from django.contrib import admin

from apps.services.models import ServiceCall


@admin.register(ServiceCall)
class ServiceCallAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'date', 'technician', 'part_name', 'defect')
    list_filter = ('date',)
    search_fields = ('ticket_number', 'part_name', 'defect')
