from django.db import models

from apps.associations.models import Association
from apps.invoices.models import Invoice
from core.models import BaseModel


class PartLabel(BaseModel):
    """Etiqueta de peça (1 por peça) — RF-06."""

    association = models.OneToOneField(
        Association,
        on_delete=models.CASCADE,
        verbose_name='Associação',
    )

    class Meta:
        verbose_name = 'Etiqueta de peça'
        verbose_name_plural = 'Etiquetas de peças'

    def __str__(self):
        return f'Etiqueta — {self.association}'


class InvoiceLabel(BaseModel):
    """Etiqueta romaneio (1 por volume) — RN-11/RN-12. ``volume_index`` de 1..N."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='labels',
        verbose_name='Nota fiscal',
    )
    volume_index = models.PositiveIntegerField(verbose_name='Índice do volume')

    class Meta:
        verbose_name = 'Etiqueta de romaneio'
        verbose_name_plural = 'Etiquetas de romaneio'
        ordering = ['volume_index']
        constraints = [
            models.UniqueConstraint(
                fields=['invoice', 'volume_index'],
                name='unique_volume_per_invoice',
            ),
        ]

    def __str__(self):
        return f'Romaneio {self.volume_index}/{self.invoice.volumes}'
