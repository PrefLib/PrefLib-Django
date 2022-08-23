from django import forms

from datetime import datetime

from .models import *


class SearchForm(forms.Form):
    data_set_extension = forms.ChoiceField(choices=DATACATEGORY + [('all', 'all')])
    num_alternatives_max = forms.IntegerField(label="Maximal number of alternatives")
    num_alternatives_min = forms.IntegerField(label="Minimal number of alternatives")
    num_voters_max = forms.IntegerField(label="Maximal number of voters")
    num_voters_min = forms.IntegerField(label="Minimal number of voters")


class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=30)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


# News form
class PaperForm(forms.Form):
    title = forms.CharField(
        label='Title',
        max_length=1000,
        widget=forms.TextInput(attrs={'style': 'width:100%;'}))

    authors = forms.CharField(
        label='Authors',
        max_length=1000,
        widget=forms.TextInput(attrs={'style': 'width:100%;'}))

    publisher = forms.CharField(
        label='Publisher',
        max_length=1000,
        widget=forms.TextInput(attrs={'style': 'width:100%;'}))

    url = forms.URLField(widget=forms.URLInput(attrs={'style': 'width:100%;'}))
    year = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(PaperForm, self).__init__(*args, **kwargs)
        now = datetime.now()
        self.fields['year'] = forms.IntegerField(
            initial=int(now.year),
            label='Year',
            max_value=int(now.year),
            min_value=2000)
