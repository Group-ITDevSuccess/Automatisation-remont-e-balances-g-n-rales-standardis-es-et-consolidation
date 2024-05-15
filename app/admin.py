from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Connexion, Societe


@admin.register(Connexion)
class ConnexionAdmin(ImportExportModelAdmin):
    list_display = ('server', 'login')
    search_fields = ('server', 'login')


@admin.register(Societe)
class SocieteAdmin(ImportExportModelAdmin):
    list_display = ('name', 'value', 'base', 'table', 'active', 'connexion', 'created_at', 'updated_at')
    search_fields = ('name', 'value', 'base', 'table')
    list_filter = ('active', 'connexion', 'created_at', 'updated_at')
    readonly_fields = ('uid', 'created_at', 'updated_at')

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.image and obj.image.path:
                obj.image.delete()
        super().delete_queryset(request, queryset)
