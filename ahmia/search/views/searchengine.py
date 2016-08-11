"""

Views
Full text search views.
YaCy back-end connections.

"""
import math
import time
from datetime import date
import urllib # URL encoding
import re

import urllib3
import simplejson as json

from django.conf import settings  # For the back-end connection settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import Context, loader
from django.views.decorators.http import require_GET, require_http_methods

@require_http_methods(["GET", "POST"])
def proxy(request):
    """Proxy connection to Elasticsearch"""
    full_url = request.get_full_path()
    http = urllib3.PoolManager()
    url = settings.PROXY_BASE_URL + full_url.replace("/elasticsearch/", "")
    content_type = {'Content-Type':request.META.get('CONTENT_TYPE')}
    response = http.request(request.method, url,
                            headers=content_type, body=request.body)
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
    RESULTS_PER_PAGE = 50
    query_string = request.GET.get('q', '')
    page = request.GET.get('page', '')
    search_time = ""
    if query_string:
        start = time.time()
        if "i2p" in request.path:
            search_results = query_object_elasticsearch(query_string,
                                                        item_type="i2p")
        else:
            search_results = query_object_elasticsearch(query_string)
        end = time.time()
        search_time = end - start
        search_time = round(search_time, 2)
    else:
        # don't query anything
        return redirect('/')

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
    result_final = result_offset + RESULTS_PER_PAGE

    max_pages = int(math.ceil(float(total_search_results) / RESULTS_PER_PAGE))
    if result_offset >= total_search_results:
        page = max_pages
        result_offset = max_pages * RESULTS_PER_PAGE
    if result_final > total_search_results:
        result_final = total_search_results

    # truncate results
    search_results = search_results[result_offset:result_final]

    if "i2p" in request.path:
        template = loader.get_template('i2p_results.html')
    else:
        template = loader.get_template('tor_results.html')

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
    pool = urllib3.HTTPConnectionPool('127.0.0.1', '9200')
    # For testing, external Elasticsearch end-point
    #pool = urllib3.HTTPSConnectionPool('ahmia.fi', '443')
    query_string = re.escape(query_string)
    query = urllib.quote_plus(query_string.encode('utf-8'))
    endpoint = '/crawl/' + item_type + '/_search/?size=100&q=' + query
    # For testing, external Elasticsearch end-point
    # endpoint =
    #    '/elasticsearch/crawl/' + item_type + '/_search/?size=100&q=' + query
    http_res = pool.request('GET', endpoint)
    res_json = http_res.data
    response = json.loads(res_json)
    results_obj = {}
    for element in response['hits']['hits']:
        element = element['_source']
        if not element.get('domain', ''):
            continue
        # Skip if there already is the most possible front page in the results
        if results_obj.has_key(element['domain']):
            if results_obj[element['domain']]['url'] == element['domain']:
                continue
        res = {
            'title': element['title'] or 'No title found',
            'description': element['text'] or 'No description found',
            'pub_date': element['timestamp'] or -1,
            'url': element['url'] or '',
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
        print "2.0*%f + 3.0*%f + 1.0*%f" % \
            self.tor2web, self.backlinks, self.clicks
    def sum(self):
        """Calculate the popularity."""
        #The model can be very simple (sum)
        #What are the proper coefficients?
        sum_function = 2.0*self.tor2web + 3.0*self.backlinks + 1.0*self.clicks
        return sum_function
    def __repr__(self):
        return repr((self.url, self.tor2web,
                     self.backlinks, self.clicks, self.sum))
