from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class ServiceCall(BaseModel):
    """Atendimento técnico (RF-01).

    RN-03/RN-05: ``part_name`` é SOMENTE visual (drag & drop). Nunca usar no
    backend para comparação/joins/matching.
    """

    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Técnico',
    )
    ticket_number = models.CharField(max_length=100, verbose_name='Número do chamado')
    serial_number = models.CharField(max_length=100, blank=True, default='', verbose_name='Número de Série')
    date = models.DateField(default=timezone.localdate, verbose_name='Data')
    part_name = models.CharField(max_length=150, verbose_name='Nome da peça')
    defect = models.CharField(max_length=255, verbose_name='Defeito')

    class Meta:
        verbose_name = 'Peça com Defeito'
        verbose_name_plural = 'Peças com Defeito'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.ticket_number} — {self.part_name}'
