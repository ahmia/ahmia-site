""" Generig help functions for the views. """
import re  # Regular expressions

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.template import Context, loader
from django.core.mail import send_mail

from ahmia.models import HiddenWebsite, HiddenWebsiteDescription

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

def html_escape(text):
    """Produce entities within text."""
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;"
    }
    return "".join(html_escape_table.get(c, c) for c in text)

def is_valid_onion(url):
    """Test if an url is a valid hiddenservice url"""
    return re.match(r"^[a-z2-7]{16}(\.onion)?", url.strip())

def validate_onion_url(url):
    """ Test is url correct onion URL."""
    #Must be like http://3g2upl4pq6kufc4m.onion/
    if len(url) != 30:
        raise ValidationError(u'%s length is not 30' % url)
    if url[0:7] != 'http://':
        raise ValidationError(u'%s is not beginning with http://' % url)
    if url[-7:] != '.onion/':
        raise ValidationError(u'%s is not ending with .onion/' % url)
    if not re.match("[a-z2-7]{16}", url[7:-7]):
        raise ValidationError(u'%s is not valid onion domain' % url)

def render_page(page, show_descriptions=False):
    """ Return a page without any parameters """
    onions = HiddenWebsite.objects.filter(online=True)
    template = loader.get_template(page)
    if show_descriptions:
        descs = latest_descriptions(onions)
        content = Context({
            'description_list': descs,
            'count_banned': onions.filter(banned=True).count(),
            'count_online': onions.filter(banned=False).count()
        })
    else:
        content = Context({'count_banned': onions.filter(banned=True).count(),
                           'count_online': onions.filter(banned=False).count()})
    return HttpResponse(template.render(content))
