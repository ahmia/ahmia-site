"""

Views
Statistics: JSON data API and JavaScript viewers.

"""
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.core import serializers
from ahmia import view_help_functions # My view_help_functions.py
import random
from ahmia.models import HiddenWebsitePopularity

def stats(request):
    """Return stats as JSON according to different GET query parameters."""
    if request.method == 'GET':
        offset = request.GET.get('offset', '0')
        limit = request.GET.get('limit', '10')
        order_by = request.GET.get('order_by', 'public_backlinks')
        return build_stats(offset, limit, order_by)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

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
    # For each number of clicks add some noise
    for result in query_result:
        clicks = result.clicks
        clicks = clicks + random.randrange(-1, 2)
        if clicks < 0:
            clicks = random.randrange(1, 2)
        result.clicks = clicks
    response_data = serializers.serialize('json', query_result, indent=2,
    fields=('about', 'tor2web', 'public_backlinks', 'clicks'))
    return HttpResponse(response_data, content_type="application/json")

def statsviewer(request):
    """Opens JavaScript based stats viewer."""
    if request.method == 'GET':
        return view_help_functions.render_page('statistics.html')
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")
