import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.audit import get_current_user


class BaseModel(models.Model):
    """Base de todas as entidades de domínio.

    - PK UUID (id)
    - Auditoria de timestamps (created_at/updated_at) e responsáveis
      (created_by/updated_by), preenchidos automaticamente via AuditMiddleware.
    - Soft-delete via archived_at (archive()/unarchive()/is_archived).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Editado em')
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name='Arquivado em')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Criado por',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Editado por',
    )

    class Meta:
        abstract = True

    @property
    def is_archived(self):
        return self.archived_at is not None

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user is not None and getattr(user, 'is_authenticated', False):
            if not self.created_by_id:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)

    def archive(self):
        self.archived_at = timezone.now()
        self.save(update_fields=['archived_at', 'updated_at', 'updated_by'])

    def unarchive(self):
        self.archived_at = None
        self.save(update_fields=['archived_at', 'updated_at', 'updated_by'])
