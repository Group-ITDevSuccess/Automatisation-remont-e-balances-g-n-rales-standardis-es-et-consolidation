from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Connexion, Societe
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget


class SocieteResource(resources.ModelResource):
    connexion = fields.Field(column_name='connexion', attribute='connexion',
                             widget=ForeignKeyWidget(Connexion, 'server'))

    class Meta:
        model = Societe
        fields = ('uid', 'name', 'value', 'base', 'table', 'active', 'type', 'connexion')
        import_id_fields = ('uid',)


@admin.register(Connexion)
class ConnexionAdmin(admin.ModelAdmin):
    list_display = ('server', 'login', 'password')
    search_fields = ('server', 'login')


@admin.register(Societe)
class SocieteAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = SocieteResource
    list_display = ('name', 'value', 'base', 'table', 'active', 'connexion', 'created_at', 'updated_at')
    search_fields = ('name', 'value', 'base', 'table')
    list_filter = ('active', 'connexion', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
