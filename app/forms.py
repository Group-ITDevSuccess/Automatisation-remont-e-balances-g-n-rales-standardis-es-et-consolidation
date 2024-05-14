from django import forms
from django.contrib.auth.forms import UserChangeForm

from app.models import Societe
from guard.models import CustomUser


class SearchForm(forms.Form):
    debut = forms.DateField(
        label='Début',
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'type': 'date', 'class': 'form-control'})
    )

    fin = forms.DateField(
        label='Fin',
        widget=forms.DateInput(format='%d/%m/%Y',attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        # Dynamically populate the choices for the 'societe' field
        societe_choices = []
        societe_choices.extend(
            (societe.name, societe.name) for societe in Societe.objects.filter(active__exact=True).order_by('name')
        )

        self.fields['societe'] = forms.ChoiceField(
            choices=societe_choices,
            label='Société',
            widget=forms.Select(
                attrs={'class': 'selectpicker me-2 ', 'data-style': "btn-primary", "data-live-search": "true",
                       "data-header": "Choisir un Societe...", "data-size": "8"}),
            required=True
        )


class ChoiseForm(forms.Form):
    filtre = forms.MultipleChoiceField(
        label='Depot',
        widget=forms.SelectMultiple(
            attrs={
                'class': 'selectpicker me-2 ',
                'data-live-search': 'true',
                'data-live-search-placeholder': 'Search',
                'tabindex': '-98',
                'data-selected-text-format': "count",
                'data-actions-box': 'true',
                'data-size': 10,
                'multiple': 'multiple'
            }
        ),
        required=False,

    )

    def __init__(self, *args, **kwargs):
        super().__init__()
        choices = kwargs.pop('filter_choices', None)
        if choices:
            self.fields['filtre'].choices = choices


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }
