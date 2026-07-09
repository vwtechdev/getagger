from django.conf import settings
from django.db import models

from core.models import BaseModel


class Invoice(BaseModel):
    TYPE_CHOICES = [
        ('outgoing', 'Saída'),
        ('incoming', 'Entrada'),
    ]

    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Técnico',
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='outgoing', verbose_name='Tipo')
    number = models.CharField(max_length=50, verbose_name='NF-e número')
    return_code = models.CharField(max_length=50, blank=True, default='', verbose_name='Código de devolução')
    return_refs = models.CharField(max_length=500, blank=True, default='', verbose_name='RETORNO REF. NF')
    volumes = models.PositiveIntegerField(default=1, verbose_name='Volumes')

    class Meta:
        verbose_name = 'Nota fiscal'
        verbose_name_plural = 'Notas fiscais'
        ordering = ['-created_at']

    def __str__(self):
        tipo = self.get_type_display()
        if self.type == 'incoming':
            return f'NF-e {self.number} ({self.return_code}) — {tipo}'
        return f'NF-e {self.number} — {tipo}'


class InvoiceItem(BaseModel):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Nota fiscal',
    )
    product_code = models.CharField(max_length=50, verbose_name='Código do produto')
    description = models.CharField(max_length=500, verbose_name='Descrição')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')

    class Meta:
        verbose_name = 'Item da nota fiscal'
        verbose_name_plural = 'Itens da nota fiscal'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.product_code} — {self.description[:40]}'