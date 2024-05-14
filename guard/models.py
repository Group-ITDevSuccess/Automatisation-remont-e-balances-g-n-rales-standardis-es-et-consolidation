import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    LEVEL = (
        (0, '(Aucun)'),
        (1, 'Magasinier'),
        (2, 'Resp. Magasinier'),
        (3, 'RCI ou RAF'),
        (4, 'Superviseur')
    )
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    autoriser = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, blank=True, related_name='custom_users')
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name='custom_users')
    level = models.IntegerField(choices=LEVEL, null=True, default=0)

    def __str__(self):
        return self.username
