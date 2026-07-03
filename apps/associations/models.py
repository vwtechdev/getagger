from django.db import models

from apps.invoices.models import InvoiceItem
from apps.services.models import ServiceCall
from core.models import BaseModel


class Association(BaseModel):
    """Vínculo permanente e manual (RN-06) entre atendimento e item da NF (1:1)."""

    service_call = models.OneToOneField(
        ServiceCall,
        on_delete=models.PROTECT,
        verbose_name='Atendimento',
    )
    invoice_item = models.OneToOneField(
        InvoiceItem,
        on_delete=models.PROTECT,
        verbose_name='Item da nota fiscal',
    )

    class Meta:
        verbose_name = 'Associação'
        verbose_name_plural = 'Associações'

    def __str__(self):
        return f'{self.invoice_item} ↔ {self.service_call}'
