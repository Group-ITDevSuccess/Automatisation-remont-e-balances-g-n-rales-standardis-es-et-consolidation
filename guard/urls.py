from django.urls import path

from guard import views

app_name = 'auths'
urlpatterns = [
    path('administation/', views.administration, name='administration'),
    path('login/', views.LoginLDAP.as_view(), name='login'),
    path('logout/', views.logout_ldap, name='logout'),
    path('updates/', views.update_field, name='update_field'), # type: ignore
    path('delete-user/<str:uid>/', views.delete_user, name='delete_user'),
]
