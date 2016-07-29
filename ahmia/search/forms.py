"""Forms used in Ahmia."""

from django import forms
from django.utils.translation import ugettext as _

class SearchForm(forms.Form):
    """ Form used by the search query """
    query = forms.CharField(
        widget=forms.TextInput(
            attrs={'placeholder': _('Enter your .onion address here')}
        )
    )
    page = forms.IntegerField()
