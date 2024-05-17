from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),
    path('get-data-for-table/', views.get_data_for_event, name='get-data-for-table'),
    path('add-data-for-table/', views.add_data_for_event, name='add-data-for-table'),
]
