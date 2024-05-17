from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Connexion, Societe, Compte, Balance, Events
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget


class SocieteResource(resources.ModelResource):
    connexion = fields.Field(column_name='connexion', attribute='connexion',
                             widget=ForeignKeyWidget(Connexion, 'server'))

    class Meta:
        model = Societe
        fields = ('uid', 'name', 'value', 'base', 'table', 'active', 'type', 'connexion')
        import_id_fields = ('uid',)


class CompteResource(resources.ModelResource):
    class Meta:
        model = Compte
        fields = ('societe', 'compte_sage', 'compte_unif', 'uid')
        import_id_fields = ('uid',)


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = (
    'societe', 'compte_sage', 'compte_unif', 'designation', 'debit', 'credit', 'montant', 'created_at', 'updated_at')
    list_filter = ('societe',)
    search_fields = ('compte_sage', 'compte_unif', 'designation')


@admin.register(Events)
class EventsAdmin(admin.ModelAdmin):
    list_display = ('uid', 'date',)
    search_fields = ('date',)
    list_per_page = 20


@admin.register(Compte)
class CompteAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = CompteResource
    list_display = ('societe', 'compte_sage', 'compte_unif')


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
