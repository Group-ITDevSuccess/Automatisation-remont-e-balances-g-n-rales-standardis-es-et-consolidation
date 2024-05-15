from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),
    path('get-data-for-table/', views.get_data_for_table, name='get-data-for-table'),
]
