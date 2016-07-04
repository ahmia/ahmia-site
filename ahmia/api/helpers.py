from django.http import HttpResponse
from django.template import Context, loader

from ahmia.models import HiddenWebsiteDescription

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
    content = Context({
        'message': message,
        'time': time,
        'redirect': url
    })
    return HttpResponse(template.render(content))
