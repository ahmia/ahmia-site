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
def legal(request):
    """Static legal page."""
    return helpers.render_page('static/legal.html')

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
    return helpers.render_page('static/about.html')

@require_GET
def show_ip(request):
    """Returns the IP address of the request."""
    ip_addr = helpers.get_client_ip(request)
    return HttpResponse(ip_addr)

@require_GET
def gsoc(request):
    """Summer of code 2014."""
    return helpers.render_page('static/gsoc.html')
