import os
import uuid

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone


def image_upload_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    unique_filename = f"{instance.uid}{file_extension}"
    return f"image/{unique_filename}"


class Connexion(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.CharField(verbose_name='Server', max_length=150, unique=True)
    login = models.CharField(verbose_name='Identifiant', max_length=50, null=True, default='reader')
    password = models.CharField(verbose_name='Mot de Passe', max_length=500, default='m1234')

    def __str__(self):
        return self.server


class Societe(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to=image_upload_path, null=True, blank=True, default='')
    name = models.CharField(verbose_name='Name', max_length=150, unique=True)
    value = models.CharField(max_length=150)
    base = models.CharField(max_length=150)
    table = models.CharField(max_length=150, blank=True, null=True, default='')
    active = models.BooleanField(default=True)
    type = models.CharField(max_length=150, null=True, blank=True, choices=[('X3', 'X3'), ('SAGE100', 'SAGE100')])
    connexion = models.ForeignKey(Connexion, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Compte(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    societe = models.CharField(max_length=150, null=True, blank=True)
    compte_sage = models.CharField(max_length=150, null=True, blank=True)
    compte_unif = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return self.societe


class Balance(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    societe = models.ForeignKey(Societe, on_delete=models.CASCADE, null=True, blank=True)
    compte_sage = models.CharField(max_length=150, null=True, blank=True)
    compte_unif = models.CharField(max_length=150, null=True, blank=True)
    designation = models.TextField(blank=True, null=True)
    target = models.IntegerField(blank=False)
    debit = models.FloatField(default=0)
    credit = models.FloatField(default=0)
    montant = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.societe.name


@receiver(pre_delete, sender=Societe)
def delete_societe_image(sender, instance, **kwargs):
    if instance.image and instance.image.path:
        instance.image.delete()

    class Meta:
        verbose_name = 'Authentification et Sécurité'
        verbose_name_plural = 'Authentification'

    def get_name_access(self):
        return self.access.all().values_list('uid', flat=True)
