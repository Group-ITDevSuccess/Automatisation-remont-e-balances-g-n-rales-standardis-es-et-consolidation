import json

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from app.models import Societe
from utils.ldap import ldap_login_connection, write_log
from utils.script import are_valid_uuids
from .forms import LoginForm, ProfileForm
from .models import CustomUser


def is_user_not_authenticated(user):
    return not user.is_authenticated


class LoginLDAP(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('app:index')

        form = LoginForm()  # Use singular form name for consistency
        context = {'form': form}
        return render(request, 'guard/login.html', context)

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if username not in ['admin.dev', 'user.dev']:
                try:
                    user = CustomUser.objects.get(username=username)
                    if user.autoriser:
                        connection_info = ldap_login_connection(username=username, password=password)
                        if isinstance(connection_info, dict):
                            if user.last_name == '' or user.first_name == '':
                                email = connection_info.get('email', '')
                                last_name = connection_info.get('lastname', '')
                                first_name = connection_info.get('firstname', '')

                                user.last_name = last_name
                                user.first_name = first_name
                                user.email = email
                                user.save()
                            login(request, user)
                            return redirect('app:index')
                        else:
                            messages.error(request, "Identifiant ou mot de passe incorrecte, réessayez !")
                    else:
                        messages.error(request, "Vous n'êtes pas encore autorisé à vous connecter à cette plateforme !")
                except CustomUser.DoesNotExist:
                    connection_info = ldap_login_connection(username=username, password=password)
                    if connection_info:
                        email = connection_info.get('email', '')
                        last_name = connection_info.get('lastname', '')
                        first_name = connection_info.get('firstname', '')

                        user = CustomUser(
                            username=username,
                            last_name=last_name,
                            first_name=first_name,
                            email=email,
                            is_staff=False,
                            is_superuser=False,
                            autoriser=False
                        )
                        user.save()
                        messages.success(request, "Accès en attente de validation. Veuillez contacter le support !")
                    else:
                        messages.error(request, "Identifiant ou mot de passe incorrecte, réessayez !")
                except Exception as e:
                    messages.error(request,
                                   "Une erreur s'est produite lors de la connexion. Veuillez contacter le support !")
                    write_log(str(e))
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('app:index')
                else:
                    messages.error(request, "Authentification incorrecte")
        else:
            messages.error(request, "Formulaire invalide !")

        return redirect('auths:login')


@login_required
def logout_ldap(request):
    msg = f"Au-revoir {request.user.last_name} {request.user.first_name}"
    all_message = messages.get_messages(request)
    if all_message:
        for message in all_message:
            if message.tags == 'success':
                message.used = True

    logout(request)
    messages.success(request, msg)
    return redirect('auths:login')


# Create your views here.
@login_required
def profile(request):
    user = get_object_or_404(CustomUser, username=request.user)
    if request.method == 'POST':
        forms = ProfileForm(request.POST, instance=user)
        if forms.is_valid():
            forms.save()
            messages.success(request, 'Sauvegarder avec Success!')
            return redirect('auths:profile')
    else:
        user, create = CustomUser.objects.get_or_create(username=request.user)
        forms = ProfileForm(instance=user)

    context = {
        'form': forms,
        'path': request.path
    }
    return render(request, 'guard/profile.html', context)


@csrf_exempt
@login_required
def update_field(request):
    body = json.loads(request.body)
    print(body)
    try:
        uid = are_valid_uuids(body['uid'])
        if uid is not None:
            fieldset = CustomUser.objects.get(uid=uid)
            for key, value in body.items():
                if key != 'uid':
                    setattr(fieldset, key, value)
            fieldset.save()
            # Manually creating the data dictionary
            data = [{
                'uid': fieldset.uid,
                'username': fieldset.username,
                'first_name': fieldset.first_name,
                'last_name': fieldset.last_name,
                'email': fieldset.email,
                'autoriser': fieldset.autoriser,
                'is_active': fieldset.is_active,
                'is_staff': fieldset.is_staff,
                'is_superuser': fieldset.is_superuser,
                'date_joined': fieldset.date_joined,
            }]
            response_data = {'status': 'success', 'data': data}
            return JsonResponse(response_data)

    except Exception as e:
        write_log(str(e))
    return JsonResponse({'status': 'success', 'message': "Une erreur à survenue !"})


@login_required
def delete_user(request, uid):
    user = get_object_or_404(CustomUser, uid=uid)
    user.delete()
    messages.success(request, "Utilisateur Supprimer")
    return redirect('app:index')


@csrf_exempt
@login_required
def get_users(request):
    body = json.loads(request.body)
    users = CustomUser.objects.all().values(
        'uid', 'username', 'first_name', 'last_name', 'email', 'autoriser',
        'is_active', 'is_staff', 'is_superuser', 'date_joined').order_by('-date_joined')
    data = [{key: value for key, value in user.items()} for user in users]
    return JsonResponse({'last_page': body['page'], 'data': data})


@login_required
def administration(request):
    return render(request, 'guard/administration.html', {
        'path': request.path
    })
