from django.contrib import admin

from apps.invoices.models import Invoice, InvoiceItem


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'return_code', 'volumes', 'technician', 'created_at')
    search_fields = ('number', 'return_code')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'description', 'invoice')
    search_fields = ('product_code', 'description')
