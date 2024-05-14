from django import forms

from guard.models import CustomUser


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control '}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom de famille',
            'email': 'Adresse e-mail'
        }


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        label='Identifiant',
        widget=forms.TextInput(attrs={'class': 'form-control rounded-left', 'placeholder': 'Identifiant'}),
        error_messages={'invalid': 'A valid identification is required!'}
    )

    password = forms.CharField(
        label='Mot de Passe',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control rounded-left', 'placeholder': 'Mot de Passe', 'autocomplete': "off"}),
        min_length=2,
        error_messages={'min_length': 'Password must be at least 8 characters!'}

    )
