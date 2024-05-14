from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy

from app.models import Societe


class CustomUser(AbstractUser):
    autoriser = models.BooleanField(default=False,
                                    help_text=gettext_lazy("Autoriser l'utilisateur à se connecter au plateforme."))

    groups = models.ManyToManyField(Group, blank=True, related_name='custom_users')
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name='custom_users')
    access = models.ManyToManyField(Societe, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Authentification et Sécurité'
        verbose_name_plural = 'Authentification'
