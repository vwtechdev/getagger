from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class ServiceCall(BaseModel):
    STATUS_CHOICES = [
        ('new', 'Peça nova'),
        ('attended', 'Peça com defeito'),
    ]

    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Técnico',
    )
    ticket_number = models.CharField(max_length=100, blank=True, default='', verbose_name='Número do chamado')
    serial_number = models.CharField(max_length=100, blank=True, default='', verbose_name='Número de Série')
    date = models.DateField(default=timezone.localdate, verbose_name='Data')
    part_name = models.CharField(max_length=150, verbose_name='Nome da peça')
    defect = models.CharField(max_length=255, blank=True, default='', verbose_name='Defeito')
    source_invoice_number = models.CharField(max_length=50, blank=True, default='', verbose_name='NF de saída (texto)')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    returned_qty = models.PositiveIntegerField(default=0, verbose_name='Quantidade devolvida')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', verbose_name='Status')
    source_invoice = models.ForeignKey(
        'invoices.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_calls',
        verbose_name='NF de origem (saída)',
    )
    destination_invoice = models.ForeignKey(
        'invoices.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='destination_calls',
        verbose_name='NF de destino (entrada)',
    )

    class Meta:
        verbose_name = 'Peça com Defeito'
        verbose_name_plural = 'Peças com Defeito'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.ticket_number or "(sem chamado)"} — {self.part_name}'