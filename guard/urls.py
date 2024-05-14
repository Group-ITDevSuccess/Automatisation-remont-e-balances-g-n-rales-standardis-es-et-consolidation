from django.urls import path

from guard import views

app_name = 'auths'
urlpatterns = [
    path('login/', views.LoginLDAP.as_view(), name='login'),
    path('logout/', views.logout_ldap, name='logout'),
    path('update/', views.update_field, name='update_field'),
    path('delete-user/<str:uid>/', views.delete_user, name='delete_user'),
]
