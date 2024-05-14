from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from app.models import Connexion, Societe


class ConnexionResource(resources.ModelResource):
    class Meta:
        model = Connexion
        fields = ('uid', 'server', 'types', 'login', 'password', 'created_at', 'updated_at')
        import_id_fields = ('uid',)


class SocieteResource(resources.ModelResource):
    connexion = fields.Field(column_name='connexion', attribute='connexion', widget=ForeignKeyWidget(Connexion, 'server'))

    class Meta:
        model = Societe
        fields = ('uid', 'name', 'value', 'base', 'connexion', 'created_at', 'updated_at')
        import_id_fields = ('uid',)


@admin.register(Connexion)
class ConnexionAdmin(admin.ModelAdmin):
    list_display = ('server', 'types', 'login', 'password',)
    fieldsets = [
        (None, {
            'fields': ('server', 'types', 'login', 'password')
        }),
        ('Date', {
            'classes': ('collapse', 'collapse-close'),
            'fields': ('created_at', 'updated_at')
        })
    ]

    readonly_fields = ['created_at', 'updated_at']


@admin.register(Societe)
class SocieteAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = SocieteResource
    list_display = ('name', 'active', 'value', 'base', 'connexion', 'created_at', 'updated_at')
    fieldsets = [
        (None, {
            'fields': ('name', 'active', 'value', 'base', 'connexion')
        }),
        ('Date', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        })
    ]
    readonly_fields = ['created_at', 'updated_at']
