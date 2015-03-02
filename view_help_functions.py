""" Generig help functions for the views. """
import re  # Regular expressions

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.template import Context, loader

from ahmia.models import HiddenWebsite, HiddenWebsiteDescription


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

def latest_descriptions(onions):
    """Return the latest descriptions to these onion objects."""
    #The old implementatation was working only with PostgreSQL database
    #desc = HiddenWebsiteDescription.objects.order_by('about', '-updated')
    #desc = desc.distinct('about')
    # Select the onions related to the descriptions
    descriptions = HiddenWebsiteDescription.objects.select_related("about")
    # Select only the onions, online ones
    descriptions = descriptions.filter(about__in=onions)
    # Order the results
    descriptions = descriptions.order_by('about', '-updated')
    descs = []
    last_onion = "" # The latest onion selected
    # Select the first (the latest) from each onion group
    for desc in descriptions:
        if last_onion != desc.about.id:
            last_onion = desc.about.id
            desc.url = desc.about.url
            desc.hs_id = desc.about.id
            desc.banned = desc.about.banned
            descs.append(desc)
    return descs

def render_page(page, show_descriptions=False):
    """ Return a page without any parameters """
    onions = HiddenWebsite.objects.filter(online=True)
    template = loader.get_template(page)
    if show_descriptions:
        descs = latest_descriptions(onions)
        content = Context({'description_list': descs,
        'count_banned': onions.filter(banned=True).count(),
        'count_online': onions.filter(banned=False).count()})
    else:
        content = Context({'count_banned': onions.filter(banned=True).count(),
        'count_online': onions.filter(banned=False).count()})
    return HttpResponse(template.render(content))

def get_client_ip(request):
    """Returns the IP address of the HTTP request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_addr = x_forwarded_for.split(',')[0]
    else:
        ip_addr = request.META.get('REMOTE_ADDR')
    return ip_addr

def redirect_page(message, time, url):
    """Build and return redirect page."""
    template = loader.get_template('redirect.html')
    content = Context({'message': message,
    'time': time,
    'redirect': url})
    return HttpResponse(template.render(content))

def round_to_next_multiple_of(number, divisor):
    """
    Return the lowest x such that x is at least the number
    and x modulo divisor == 0
    """
    number = number + divisor - 1
    number = number - number % divisor
    return number
