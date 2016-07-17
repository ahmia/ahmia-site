"""
Views
Full text search views.
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

class OnionRedirectView(RedirectView):
    permanent = False
    query_string = False
    http_method_names = ['get']

    def update_stat_counter(self):
        pass

    def get_redirect_url(self, *args, **kwargs):
        redirect_url = request.GET.get('redirect_url', '')
        if not redirect_url:
            answer = "Bad request: no GET parameter URL."
            return None
        self.update_stat_counter()
        return redirect_url

class TorResultsView(TemplateView):
    http_method_names = ['get']
    template_name = "tor_results.html"
    RESULTS_PER_PAGE = 50

    def get_pool(self):
        #pool = urllib3.HTTPSConnectionPool(settings.ELASTICSEARCH_HOST,
        #        settings.ELASTICSEARCH_PORT,
        #        assert_fingerprint=settings.ELASTICSEARCH_TLS_FPRINT)
        pool = urllib3.HTTPConnectionPool('127.0.0.1', '9200')
        # For testing, external Elasticsearch end-point
        #pool = urllib3.HTTPSConnectionPool('ahmia.fi', '443')

    def get_endpoint(self, query, page):
        # For testing, external Elasticsearch end-point
        # endpoint =
        #    '/elasticsearch/crawl/' + item_type + '/_search/?size=100&q=' + query
        query = urllib.quote_plus(re.escape(query).encode('utf-8'))
        return '/crawl/tor/_search/?size=100&q=' + query

    def request_elasticsearch(self, query, page):
        """Return a dict of Elasticsearch results."""
        try:
            return self.get_pool().request(
                'GET',
                self.get_endpoint(query, page)
            )
        except:
            return None

    def format_response(self, request):
        return json.loads(response.data)

    def get_context_data(self, **kwargs):
        query_string = request.GET.get('q', '')
        page = request.GET.get('page', 0)
        search_time = ""
        # assert query_string not None
        start = time.time()

        response = self.request_elasticsearch(query_string, page)
        length, results = self.format_response(response)

        end = time.time()
        search_time = end - start
        search_time = round(search_time, 2)

        max_pages = int(math.ceil(float(length) / self.RESULTS_PER_PAGE))

        return {
            'page': page,
            'max_pages': max_pages,
            'result_begin': ,
            'result_end': ,
            'total_search_results': length,
            'query_string': query_string,
            'search_results': results,
            'search_time': search_time,
            'now': date.fromtimestamp(time.time())
        }

class IipResultsView(TorResultsView):
    def get_endpoint(self, query):
        return '/crawl/i2p/_search/?size=100&q=' + query
