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
    if request.method == 'POST':
        try:
            field_id = request.POST.get('field_id')
            field = request.POST.get('field')
            checked = request.POST.getlist('value[]')  # Changé de 'value' à 'checked'
            if field == 'status':
                fieldset = get_object_or_404(Societe, uid=field_id)
                field = 'active'
            elif field == 'application':
                fieldset = get_object_or_404(Societe, uid=field_id)
            else:
                fieldset = get_object_or_404(CustomUser, uid=field_id)
            val = are_valid_uuids(checked)
            if not val:
                if checked[0].lower() == 'true':
                    checked = True
                elif checked[0].lower() == 'false':
                    checked = False
                setattr(fieldset, field, checked)
                fieldset.save()

            else:
                societe = Societe.objects.filter(uid__in=checked)

                fieldset = get_object_or_404(CustomUser, uid=field_id)
                fieldset.access.clear()
                fieldset.access.add(*societe)

            response_data = {'status': 'success', 'message': 'Données mises à jour avec succès.'}
            return JsonResponse(response_data)

        except Exception as e:
            write_log(str(e))
            return JsonResponse({'status': f'error !'})


@login_required
def delete_user(request, uid):
    user = get_object_or_404(CustomUser, uid=uid)
    user.delete()
    messages.success(request, "Utilisateur Supprimer")
    return redirect('app:index')
