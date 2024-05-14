from django.contrib import messages
from django.contrib.auth import login, logout
from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from utils.ldap import ldap_login_connection
from .forms import LoginForm, ProfileForm
from .models import CustomUser

# Create your views here.
from django.contrib.auth.decorators import user_passes_test


def is_user_not_authenticated(user):
    return not user.is_authenticated


class LoginLDAP(View):
    @staticmethod
    @user_passes_test(is_user_not_authenticated, login_url='app:get')
    def get(request):
        forms = LoginForm
        context = {
            'form': forms,
        }
        return render(request, 'guard/login.html', context)

    @staticmethod
    def post(request):
        forms = LoginForm(request.POST)
        if forms.is_valid():
            username = forms.cleaned_data['username']
            password = forms.cleaned_data['password']

            connexion = ldap_login_connection(username=username, password=password)
            if connexion:
                try:
                    user_get = CustomUser.objects.get(username__exact=username)
                    if user_get.autoriser:
                        login(request, user_get)
                        return redirect('app:get')
                    else:
                        messages.error(request,
                                       "Vous n'êtes pas encore autorisé à vous connecter à la plateforme Sage !")
                        return redirect('guard:login')
                except Exception as e:
                    email = connexion.get('email', '')
                    lastname = connexion.get('lastname', '')
                    firstname = connexion.get('firstname', '')
                    write_log(f"Erreur LoginLDAP : {str(e)}")

                    user_get = CustomUser(
                        username=username,
                        last_name=lastname,
                        first_name=firstname,
                        email=email,
                        autoriser=False,
                        is_staff=False,
                        is_superuser=False
                    )
                    user_get.save()
                    messages.success(request,
                                     "Votre compte a été créé. Contactez le service Sage ou DSI pour valider votre "
                                     "accès !")
                    return redirect('guard:login')

            else:
                messages.error(request, "Login ou Mot de passe Incorrect !")
                return redirect('guard:login')
        else:
            messages.error(request, "Le formulaire de connexion est invalide !")
            return redirect('guard:login')


@login_required
def logout_ldap(request):
    msg = f"Au-revoir {request.user.last_name} {request.user.first_name} !"
    all_message = messages.get_messages(request)
    if all_message:
        for message in all_message:
            if message.tags == 'success':
                message.used = True

    logout(request)
    messages.success(request, msg)
    return redirect('guard:login')


# Create your views here.
@login_required
def profile(request):
    user = get_object_or_404(CustomUser, username=request.user)
    # write_log(f"User : {user}", level=logging.INFO)
    if request.method == 'POST':
        forms = ProfileForm(request.POST, instance=user)
        # write_log(f"Forms : {forms}", level=logging.INFO)
        if forms.is_valid():
            forms.save()
            messages.success(request, 'Sauvegarder avec Success!')
            return redirect('guard:profile')
    else:
        user, create = CustomUser.objects.get_or_create(username=request.user)
        forms = ProfileForm(instance=user)

    context = {
        'form': forms,
        'path': request.path
    }
    return render(request, 'guard/profile.html', context)
