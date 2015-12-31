"""

Views
Full text search views.
YaCy back-end connections.

"""
import math
import time
from datetime import date

import simplejson as json
import urllib3  # HTTP conncetions
from django.conf import settings  # For the back-end connection settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import Context, loader
from django.views.decorators.http import require_GET, require_http_methods

from ahmia.models import HiddenWebsite, HiddenWebsitePopularity

@require_http_methods(["GET", "POST"])
def proxy(request):
    """Proxy connection to Elasticsearch"""
    full_url = request.get_full_path()
    http = urllib3.PoolManager()
    url = settings.PROXY_BASE_URL + full_url.replace("/elasticsearch/", "")
    content_type = {'Content-Type':request.META.get('CONTENT_TYPE')}
    response = http.request(request.method, url, headers=content_type, body=request.body)
    r_type = response.getheader('content-type')
    r_data = response.data
    r_status = response.status
    return HttpResponse(content=r_data, content_type=r_type, status=r_status)

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
def results(request):
    """Search results page."""
    RESULTS_PER_PAGE = 20
    query_string = request.GET.get('q', '')
    page  = request.GET.get('page', '')
    search_time = ""
    if query_string:
        start = time.time()
        if "i2p" in request.path:
            search_results = query_object_elasticsearch(query_string, item_type="i2p")
        else:
            search_results = query_object_elasticsearch(query_string)
        end = time.time()
        search_time = end - start
        search_time = round(search_time, 2)
    else:
        # don't query anything
        redirect('/')
        return

    # fake paginate results
    if page:
        try:
            page = int(page) - 1
        except:
            page = 0
    else:
        page = 0

    total_search_results = len(search_results)

    # calculate offsets
    result_offset = page * RESULTS_PER_PAGE
    result_final  = result_offset + RESULTS_PER_PAGE

    max_pages = int(math.ceil(float(total_search_results) / RESULTS_PER_PAGE))
    if result_offset >= total_search_results:
        page = max_pages
        result_offset = max_pages * RESULTS_PER_PAGE
    if result_final > total_search_results:
        result_final = total_search_results

    # truncate results
    search_results = search_results[result_offset:result_final]

    template = loader.get_template('results.html')
    content = Context({
        'page': page+1,
        'max_pages': max_pages,
        'result_begin': result_offset+1,
        'result_end': result_final,
        'total_search_results': total_search_results,
        'query_string' : query_string,
        'search_results': search_results,
        'search_time': search_time,
        'now': date.fromtimestamp(time.time())
        })
    return HttpResponse(template.render(content))

def query_object_elasticsearch(query_string, item_type="tor"):
    """Return a dict of Elasticsearch results."""
    # make an http request to elasticsearch
    #pool = urllib3.HTTPSConnectionPool(settings.ELASTICSEARCH_HOST,
    #        settings.ELASTICSEARCH_PORT,
    #        assert_fingerprint=settings.ELASTICSEARCH_TLS_FPRINT)
    pool = urllib3.HTTPSConnectionPool('127.0.0.1', '9200')
    endpoint = '/elasticsearch/crawl/' + item_type + '/_search'
    query_data = { 'q': str(query_string) }
    response = json.loads(pool.request('GET', endpoint, query_data).data)
    results_obj = {}
    for element in response['hits']['hits']:
        element = element['_source']
        res = {
            'title': element['title'] or 'No title found',
            'description': element['text'] or 'No description found',
            'pub_date': element['timestamp'] or -1,
            'domain': element['domain'] or ''
        }
        timestamp = time.strptime(element['timestamp'], '%Y-%m-%dT%H:%M:%S')
        res['date'] = date.fromtimestamp(time.mktime(timestamp))
        res['timestamp'] = int(time.mktime(timestamp))
        url = element['domain'] or ''
        if '.onion' in url:
            res['url_tor2web'] = url.replace('.onion', '.tor2web.org')
        res['url'] = url
        results_obj[res['domain']] = res
    return results_obj.values()

def add_result(answer, host, results):
    """Add new search result and get the stats about it."""
    if host:
        onion_id = host.replace(".onion", "")
        tor2web, backlinks, clicks = get_popularity(onion_id)
        if tor2web > 0 or backlinks > 0 or clicks > 0:
            results.append(Popularity(host, answer, tor2web, backlinks, clicks))
    else:
        results.append(Popularity(host, answer, 1, 1, 1))

def get_popularity(onion):
    """Calculate the popularity of an onion page."""
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except ObjectDoesNotExist:
        return 1, 1, 1
    if hs.banned:
        return 0, 0, 0
    try:
        pop = HiddenWebsitePopularity.objects.get(about=hs)
        clicks = pop.clicks
        public_backlinks = pop.public_backlinks
        tor2web = pop.tor2web
        return tor2web, public_backlinks, clicks
    except ObjectDoesNotExist:
        return 1, 1, 1

def sort_results(p_tuples):
    """Sort the results according to stats."""
    # Scaling the number of backlinks
    p_by_backlinks = sorted(p_tuples, key=lambda popularity: popularity.backlinks, reverse=True)
    for index, p_info in enumerate(p_by_backlinks):
        p_info.backlinks = 1 / (float(index) + 1)
    # Scaling the number of clicks
    p_by_clicks = sorted(p_by_backlinks, key=lambda popularity: popularity.clicks, reverse=True)
    for index, p_info in enumerate(p_by_clicks):
        p_info.clicks = 1 / (float(index) + 1)
    # Scaling the number of Tor2web
    p_by_tor2web = sorted(p_by_clicks, key=lambda popularity: popularity.tor2web, reverse=True)
    for index, p_info in enumerate(p_by_tor2web):
        p_info.tor2web = 1 / (float(index) + 1)
    p_by_sum = sorted(p_by_tor2web, key=lambda popularity: popularity.sum(), reverse=True)
    html_answer = ""
    for p_info in p_by_sum:
        html_answer = html_answer + p_info.content
    return html_answer

class Popularity(object):
    """Popularity by Tor2web visits, backlinks and clicks."""
    def __init__(self, url, content, tor2web, backlinks, clicks):
        self.url = url
        self.content = content
        self.tor2web = float(tor2web)
        self.backlinks = float(backlinks)
        self.clicks = float(clicks)
    def func(self):
        """Print the sum function."""
        print "2.0*%f + 3.0*%f + 1.0*%f" % self.tor2web, self.backlinks, self.clicks
    def sum(self):
        """Calculate the popularity."""
        #The model can be very simple (sum)
        #What are the proper coefficients?
        sum_function = 2.0*self.tor2web + 3.0*self.backlinks + 1.0*self.clicks
        return sum_function
    def __repr__(self):
        return repr((self.url, self.tor2web, self.backlinks, self.clicks, self.sum))
