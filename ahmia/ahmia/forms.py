"""Forms used in Ahmia."""
from hashlib import md5

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext as _

from .models import HiddenWebsite
from .validators import validate_onion_url, validate_status

class AddOnionForm(forms.Form):
    """Request to add an onion domain."""
    onion = forms.CharField(validators=[validate_onion_url, validate_status])

    def add_onion(self):
        """Add an onion service to database"""
        onion_name = self.cleaned_data['onion']
        hs, creat = HiddenWebsite.objects.get_or_create(
            id=onion_name,
            url=u'http://%s/' % onion_name,
            md5=md5(onion_name).hexdigest()
        )
        if creat:
            hs.online = False
            hs.banned = False
            hs.full_clean()
            hs.save()
        info_msg = _('Your hidden service has been added.')

def send_abuse_report(onion_url=None):
    """Send an abuse report by email."""
    if onion_url is None:
        return
    if settings.DEBUG:
        return
    subject = "Hidden service abuse notice"
    message = "User sent abuse notice for onion url %s" % (onion_url)
    send_mail(subject, message,
              settings.DEFAULT_FROM_EMAIL, settings.RECIPIENT_LIST,
              fail_silently=False)
