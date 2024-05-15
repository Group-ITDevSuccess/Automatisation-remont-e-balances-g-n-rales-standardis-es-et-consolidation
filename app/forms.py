from datetime import date

from django import forms
from django.contrib.auth.forms import UserChangeForm

from app.models import Societe
from guard.models import CustomUser


class SearchForm(forms.Form):
    target = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'selectpicker'}),
        choices=[(year, str(year)) for year in range(date.today().year, 2016, -1)],
        required=True,
        label="Date antérieure",
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
