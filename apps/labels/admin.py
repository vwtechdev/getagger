from django.contrib import admin

from apps.labels.models import InvoiceLabel, LabelSettings, PartLabel


@admin.register(PartLabel)
class PartLabelAdmin(admin.ModelAdmin):
    list_display = ('service_call', 'created_at')


@admin.register(InvoiceLabel)
class InvoiceLabelAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'volume_index')


@admin.register(LabelSettings)
class LabelSettingsAdmin(admin.ModelAdmin):
    list_display = ('technician', 'page_format', 'margin', 'font_size')
    list_filter = ('page_format',)
