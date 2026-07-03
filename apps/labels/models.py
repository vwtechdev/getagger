from django.conf import settings
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


class LabelSettings(BaseModel):
    """Configuração de impressão de etiquetas por técnico."""

    PAGE_FORMATS = [
        ('A4', 'A4'),
        ('THERMAL_80MM', 'Bobina 80mm'),
    ]

    technician = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='label_settings',
        verbose_name='Técnico',
    )
    page_format = models.CharField(
        max_length=20,
        choices=PAGE_FORMATS,
        default='A4',
        verbose_name='Formato de página',
    )
    margin = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=8.0,
        verbose_name='Margem (mm)',
    )
    font_size = models.PositiveIntegerField(
        default=11,
        verbose_name='Tamanho da fonte (pt)',
    )

    class Meta:
        verbose_name = 'Configuração de etiqueta'
        verbose_name_plural = 'Configurações de etiquetas'

    def __str__(self):
        return f'{self.technician.name} — {self.get_page_format_display()}'
