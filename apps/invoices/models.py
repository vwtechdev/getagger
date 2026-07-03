from django.conf import settings
from django.db import models

from core.models import BaseModel


class Invoice(BaseModel):
    """Nota fiscal importada (PDF). RN-04: isolada por técnico.

    O PDF NÃO é persistido — usado apenas para extração do conteúdo.
    """

    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Técnico',
    )
    number = models.CharField(max_length=50, verbose_name='NF-e número')
    return_code = models.CharField(max_length=50, verbose_name='Código de devolução')
    volumes = models.PositiveIntegerField(default=1, verbose_name='Volumes')

    class Meta:
        verbose_name = 'Nota fiscal'
        verbose_name_plural = 'Notas fiscais'
        ordering = ['-created_at']

    def __str__(self):
        return f'NF-e {self.number} ({self.return_code})'


class InvoiceItem(BaseModel):
    """Item extraído da tabela 'DADOS DOS PRODUTOS / SERVIÇOS' (CÓD. PROD + DESCRIÇÃO)."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Nota fiscal',
    )
    product_code = models.CharField(max_length=50, verbose_name='Código do produto')
    description = models.CharField(max_length=500, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Item da nota fiscal'
        verbose_name_plural = 'Itens da nota fiscal'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.product_code} — {self.description[:40]}'
