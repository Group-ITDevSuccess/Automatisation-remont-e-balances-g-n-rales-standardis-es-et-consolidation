import os
import uuid

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal


def image_upload_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    unique_filename = f"{instance.uid}{file_extension}"
    return f"image/{unique_filename}"


class Connexion(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.CharField(verbose_name='Server', max_length=150)
    login = models.CharField(verbose_name='Identifiant', max_length=50, null=True, default='reader')
    password = models.CharField(verbose_name='Mot de Passe', max_length=500, default='m1234')

    def __str__(self):
        return f"{self.server}"


class Societe(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to=image_upload_path, null=True, blank=True, default='')
    name = models.CharField(max_length=150, unique=True)
    value = models.CharField(max_length=150)
    base = models.CharField(max_length=150)
    table = models.CharField(max_length=150, null=True, default='')
    active = models.BooleanField(default=True)
    connexion = models.ForeignKey(Connexion, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


@receiver(pre_delete, sender=Societe)
def delete_societe_image(sender, instance, **kwargs):
    if instance.image and instance.image.path:
        instance.image.delete()

    class Meta:
        verbose_name = 'Authentification et Sécurité'
        verbose_name_plural = 'Authentification'

    def get_name_access(self):
        return self.access.all().values_list('uid', flat=True)
