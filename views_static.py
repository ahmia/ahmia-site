"""

Views
Static HTML pages.
These pages does not require database connection.

"""
from django.http import HttpResponseNotAllowed, HttpResponse
from ahmia import view_help_functions # My view_help_functions.py

def indexing(request):
    """Static page about the indexing and crawling."""
    if request.method == 'GET':
        return view_help_functions.render_page('indexing.html')
    return HttpResponseNotAllowed("Only GET request is allowed.")

def policy(request):
    """Static policy page."""
    if request.method == 'GET':
        return view_help_functions.render_page('policy.html')
    return HttpResponseNotAllowed("Only GET request is allowed.")

def disclaimer(request):
    """Static disclaimer page."""
    if request.method == 'GET':
        return view_help_functions.render_page('disclaimer.html')
    return HttpResponseNotAllowed("Only GET request is allowed.")

def description_proposal(request):
    """Static description proposal."""
    if request.method == 'GET':
        return view_help_functions.render_page('descriptionProposal.html')
    return HttpResponseNotAllowed("Only GET request is allowed.")

def create_description(request):
    """Page to create hidden website description."""
    if request.method == 'GET':
        return view_help_functions.render_page('createHsDescription.html')
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def documentation(request):
    """Static documentation page."""
    if request.method == 'GET':
        return view_help_functions.render_page('documentation.html')
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def about(request):
    """Static about page of ahmia."""
    if request.method == 'GET':
        return view_help_functions.render_page('about.html')
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def gsoc(request):
    """Static Google Summer of Code 2014 proposal page."""
    if request.method == 'GET':
        return view_help_functions.render_page('gsoc.html')
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def show_ip(request):
    """Returns the IP address of the request."""
    if request.method == 'GET':
        ip_addr = view_help_functions.get_client_ip(request)
        return HttpResponse(ip_addr)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")
