from django.contrib import admin

from apps.labels.models import InvoiceLabel, PartLabel


@admin.register(PartLabel)
class PartLabelAdmin(admin.ModelAdmin):
    list_display = ('association', 'created_at')


@admin.register(InvoiceLabel)
class InvoiceLabelAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'volume_index')
