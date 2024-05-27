from datetime import date

from django import forms
from django.contrib.auth.forms import UserChangeForm

from guard.models import CustomUser

# Choices for years
year_choices = [('', '---')]
year_choices.extend((year, str(year)) for year in range(date.today().year, 2016, -1))

# Choices for months
month_choices = [
    ('', '---'),
    ('01', 'January'),
    ('02', 'February'),
    ('03', 'March'),
    ('04', 'April'),
    ('05', 'May'),
    ('06', 'June'),
    ('07', 'July'),
    ('08', 'August'),
    ('09', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
]


class SearchForm(forms.Form):
    target = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'selectpicker'}),
        choices=year_choices,
        required=True,
        label="Date antérieure",
    )
    begin = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'selectpicker'}),
        choices=month_choices,
        required=True,
        label="Debut",
    )
    end = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'selectpicker'}),
        choices=month_choices,
        required=True,
        label="Fin",
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
