"""

Views
Static HTML pages.
These pages does not require database connection.

"""
from django.http import HttpResponse, HttpResponseNotAllowed
from django.template import Context, loader
from django.views.decorators.http import require_GET

import view_help_functions as helpers  # My view_help_functions.py
from ahmia.models import HiddenWebsite


@require_GET
def indexing(request):
    """Static page about the indexing and crawling."""
    return helpers.render_page('indexing.html')

@require_GET
def policy(request):
    """Static policy page."""
    template = loader.get_template("policy.html")
    onions = HiddenWebsite.objects.all()
    count_online = onions.filter(banned=False, online=True).count()
    count_banned = onions.filter(banned=True, online=True).count()
    content = Context({'onions': onions, 'count_banned': count_banned,
    'count_online': count_online})
    return HttpResponse(template.render(content))

@require_GET
def disclaimer(request):
    """Static disclaimer page."""
    return helpers.render_page('disclaimer.html')

@require_GET
def description_proposal(request):
    """Static description proposal."""
    return helpers.render_page('descriptionProposal.html')

@require_GET
def create_description(request):
    """Page to create hidden website description."""
    return helpers.render_page('createHsDescription.html')
    return HttpResponseNotAllowed("Only GET request is allowed.")

@require_GET
def documentation(request):
    """Static documentation page."""
    return helpers.render_page('documentation.html')

@require_GET
def about(request):
    """Static about page of ahmia."""
    return helpers.render_page('about.html')

@require_GET
def gsoc(request):
    """Static Google Summer of Code 2014 proposal page."""
    return helpers.render_page('gsoc.html')

@require_GET
def show_ip(request):
    """Returns the IP address of the request."""
    ip_addr = helpers.get_client_ip(request)
    return HttpResponse(ip_addr)
