""" Forms """
from django import forms
from django.utils.translation import gettext_lazy as _
from .validators import validate_onion_url, validate_status

class AddOnionForm(forms.Form):
    """Request to add an onion domain."""
    onion = forms.CharField(
        label=_("Onion URL"),
        validators=[validate_onion_url, validate_status],
        widget=forms.TextInput(
            attrs={'placeholder': _('Enter your .onion address here'), 'class': 'form-control'}),
        required=True,
        max_length=255  # Consider adding constraints like max_length for better validation
    )
