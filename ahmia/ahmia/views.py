"""

Views
Static HTML pages.
These pages does not require database connection.

"""
from textwrap import dedent

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import (HttpResponse, JsonResponse)
from django.views.decorators.http import require_GET, require_http_methods
from django.template import Context, loader
from django.utils.translation import ugettext as _

from .models import HiddenWebsite, validate_onion_url
from .forms import AddOnionForm
from .helpers import (render_page, is_valid_onion, send_abuse_report,
                      get_client_ip)

# Root page views

@require_GET
def default(request):
    """The default page."""
    template = loader.get_template('index_tor.html')
    content = Context()
    return HttpResponse(template.render(content))

@require_GET
def i2p_search(request):
    """The default page."""
    template = loader.get_template('index_i2p.html')
    content = Context()
    return HttpResponse(template.render(content))

@require_GET
def indexing(request):
    """Static page about the indexing and crawling."""
    return render_page('indexing.html')

@require_GET
def legal(request):
    """Static legal page."""
    return render_page('static/legal.html')

@require_GET
def documentation(request):
    """Static documentation page."""
    return render_page('documentation.html')

@require_GET
def about(request):
    """Static about page of ahmia."""
    return render_page('static/about.html')

@require_GET
def show_ip(request):
    """Returns the IP address of the request."""
    ip_addr = get_client_ip(request)
    return HttpResponse(ip_addr)

@require_GET
def gsoc(request):
    """Summer of code 2014."""
    return render_page('static/gsoc.html')

# Documentation content

@require_GET
def description_proposal(request):
    """Static description proposal."""
    return render_page('descriptionProposal.html')

@require_GET
def create_description(request):
    """Page to create hidden website description."""
    return render_page('createHsDescription.html')
    # return HttpResponseNotAllowed("Only GET request is allowed.")

# Forms

@require_http_methods(['GET', 'POST'])
def add(request):
    """Add form for a new .onion address."""
    err_msg = None
    info_msg = None

    template_vars = {}
    if request.method == 'POST':
        form = AddOnionForm(request.POST)
        if form.is_valid():
            try:
                onion_name = form.cleaned_data['onion']
                validate_onion_url(onion_name)
                onion = HiddenWebsite.objects.get(id=onion_name)
                if onion.banned:
                    err_msg = _(dedent('''\
                    This onion is banned and cannot be added to this index.'''))
            except ValidationError:
                err_msg = _('You did not enter a valid .onion')
            except ObjectDoesNotExist:
                # ok, add a new onion
                # we dont need anything other than the service for now
                hs, creat = HiddenWebsite.objects.get_or_create(id=id_str,
                                                                url=url,
                                                                md5=md5)
                if creat:
                    hs.online = False
                    hs.banned = False
                    hs.full_clean()
                    hs.save()
                info_msg = _('Your hidden service has been added.')
        else:
            err_msg = _('You did not enter a valid .onion')

    if err_msg:
        template_vars['flash_message'] = {'error': err_msg}
    if info_msg:
        template_vars['flash_message'] = {'info': info_msg}
    template = loader.get_template("add.html")
    content = Context(template_vars)
    return HttpResponse(template.render(content))

@require_GET
def old_add(request):
    """Add form for a new .onion address."""
    template = loader.get_template("old_add.html")
    onions = HiddenWebsite.objects.all()
    count_online = onions.filter(banned=False, online=True).count()
    count_banned = onions.filter(banned=True, online=True).count()
    content = Context({'count_banned': count_banned,
                       'count_online': count_online})
    return HttpResponse(template.render(content))

@require_http_methods(['GET', 'POST'])
def blacklist_report(request):
    """Return a request page to blacklist a site."""
    if request.method == 'POST':
        if 'onion' in request.POST \
           and is_valid_onion(request.POST['onion']):
            send_abuse_report(request.POST['onion'])
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})
    else:
        if 'onion' in request.GET \
           and is_valid_onion(request.GET['onion']):
            send_abuse_report(request.GET['onion'])
            onion = request.GET['onion']
            success = True
        else:
            onion = ''
            success = False
        content = Context({
            'success': success,
            'onion': onion
        })
        template = loader.get_template('blacklist_report.html')
        return HttpResponse(template.render(content))

@require_GET
def blacklist(request):
    """Return a blacklist page with MD5 sums of banned content."""
    try:
        banned_onions = HiddenWebsite.objects.all().filter(banned=True)
    except HiddenWebsite.DoesNotExist:
        banned_onions = []
    content = Context({'banned_onions': banned_onions})
    template = loader.get_template('blacklist.html')
    return HttpResponse(template.render(content))
