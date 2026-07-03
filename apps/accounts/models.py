from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager
from core.models import BaseModel


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """Técnico (RF-02). Autenticação por e-mail + senha; permite auto-registro."""

    name = models.CharField(max_length=150, verbose_name='Nome')
    email = models.EmailField(unique=True, verbose_name='E-mail')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_staff = models.BooleanField(default=False, verbose_name='Acesso ao admin')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Data de cadastro')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'Técnico'
        verbose_name_plural = 'Técnicos'
        ordering = ['name']

    def __str__(self):
        return self.email
