"""

Views
Statistics: JSON data API and JavaScript viewers.

"""
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Context, loader
from django.views.decorators.http import require_GET

import ahmia.view_help_functions as helpers  # My view_help_functions.py
from ahmia.models import HiddenWebsite, HiddenWebsitePopularity


@require_GET
def stats(request):
    """Return stats as JSON according to different GET query parameters."""
    offset = request.GET.get('offset', '0')
    limit = request.GET.get('limit', '10')
    order_by = request.GET.get('order_by', 'public_backlinks')
    return build_stats(offset, limit, order_by)

def build_stats(offset, limit, order_by):
    """Builds the stats results."""
    try:
        offset = int(offset)
        limit = int(limit)
        order_by = str(order_by)
        if limit > 100 or limit < 1:
            return HttpResponse('Set limit between 1-100.')
        if offset > 100 or limit < 0:
            return HttpResponse('Set offset between 0-100.')
        if limit < offset:
            return HttpResponse('Set offset < limit.')
        sort_options = ['public_backlinks', 'clicks', 'tor2web']
        if not order_by in sort_options:
            sort_options = ', '.join(sort_options)
            return HttpResponse("Sort options are: " + sort_options)
        return calculate_stats(offset, limit, order_by)
    except Exception as error:
        print error
        return HttpResponseBadRequest("Bad request")

def calculate_stats(offset, limit, order_by):
    """Calculate statistics."""
    order_by = "-" + order_by # Descending ordering
    query_list = HiddenWebsitePopularity.objects.order_by(order_by)
    query_result = query_list[offset:limit]
    # Security measure: obfuscate real-time stats
    # This simple way prevents leaking too accurate stats
    # Round the clicks to the next multiple of 8
    for result in query_result:
        result.clicks = helpers.round_to_next_multiple_of(result.clicks, 8)
    response_data = serializers.serialize('json', query_result, indent=2,
    fields=('about', 'tor2web', 'public_backlinks', 'clicks'))
    return HttpResponse(response_data, content_type="application/json")

@require_GET
def statsviewer(request):
    """Opens JavaScript based stats viewer."""
    return helpers.render_page('statistics.html')

@require_GET
def onionsovertime(request):
    """Opens JavaScript based stats viewer."""
    return helpers.render_page('onions_over_time.html')

@require_GET
def services(request):
    """Opens JavaScript based port viewer."""
    return helpers.render_page('services.html')

@require_GET
def history(request):
    """Opens JavaScript based stats viewer."""
    onions = HiddenWebsite.objects.all()
    template = loader.get_template('history.html')
    content = Context({'onions': onions.filter(banned=False),
    'count_banned': onions.filter(banned=True, online=True).count(),
    'count_online': onions.filter(banned=False, online=True).count()})
    return HttpResponse(template.render(content))

@require_GET
def trafficviewer(request):
    """Opens JavaScript based traffic viewer."""
    return helpers.render_page('traffic.html')

@require_GET
def tor2web(request):
    """Opens JavaScript based traffic viewer."""
    return helpers.render_page('tor2web.html')
