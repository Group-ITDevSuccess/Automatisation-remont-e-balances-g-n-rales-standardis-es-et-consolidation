import uuid
from django.db import models


class Connexion(models.Model):
    TYPES = (
        ('x3v7', 'AGRI'),
        ('x3sql', 'SMTP'),
        ('sage100', 'Sage100')
    )
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.CharField(verbose_name='Server', max_length=150, unique=True)
    types = models.CharField(verbose_name='Type de la base', choices=TYPES, max_length=50, null=True, blank=True)
    login = models.CharField(verbose_name='Identifiant', max_length=50, null=True, default='reader')
    password = models.CharField(verbose_name='Mot de Passe', max_length=500, default='m1234')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.server


class Societe(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    value = models.CharField(max_length=150)
    active = models.BooleanField(default=False)
    base = models.CharField(max_length=150, blank=True, null=True)
    connexion = models.ForeignKey(Connexion, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
