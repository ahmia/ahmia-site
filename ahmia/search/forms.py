"""Forms used in Ahmia."""

class SearchForm(forms.Form):
    query = forms.CharField(
        widget=forms.TextInput(
            attrs={'placeholder': _('Enter your .onion address here')}
        )
    )
    page = forms.HiddenField()
