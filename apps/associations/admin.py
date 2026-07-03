from django.contrib import admin

from apps.associations.models import Association


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ('invoice_item', 'service_call', 'created_at')
