"""
Views
Full text search views.
"""
import math
import time
from datetime import date, datetime

import urllib3
import simplejson as json

from django.views.generic.base import TemplateView, RedirectView

class OnionRedirectView(RedirectView):
    permanent = False
    query_string = False
    http_method_names = ['get']

    def update_stat_counter(self):
        pass

    def get(self, request, *args, **kwargs):
        kwargs['redirect_url'] = request.GET.get('redirect_url', '')
        return super(OnionRedirectView, self).get(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        redirect_url = kwargs['redirect_url']
        if not redirect_url:
            #answer = "Bad request: no GET parameter URL."
            return None
        self.update_stat_counter()
        return redirect_url

class TorResultsView(TemplateView):
    http_method_names = ['get']
    template_name = "tor_results.html"
    RESULTS_PER_PAGE = 5

    def get_pool(self):
        #pool = urllib3.HTTPSConnectionPool(settings.ELASTICSEARCH_HOST,
        #        settings.ELASTICSEARCH_PORT,
        #        assert_fingerprint=settings.ELASTICSEARCH_TLS_FPRINT)
        pool = urllib3.HTTPConnectionPool('127.0.0.1', '9200')
        # For testing, external Elasticsearch end-point
        #pool = urllib3.HTTPSConnectionPool('ahmia.fi', '443')
        return pool

    def get_endpoint(self, query, page):
        # For testing, external Elasticsearch end-point
        # endpoint =
        #    '/elasticsearch/crawl/' + item_type + '/_search/?size=100&q=' + q
        #query = urllib.quote_plus(re.escape(query).encode('utf-8'))
        return '/crawl/tor/_search/'

    def get_data(self, query, page):
        return json.dumps({
            "query": {
                "function_score": {
                    "functions": [
                        {
                            "field_value_factor": {
                                "field": "authority",
                                "modifier": "log1p",
                                "factor": 100000
                            }
                        }
                    ],
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "type":   "most_fields",
                                        "fields": [
                                            "fancy",
                                            "fancy.stemmed",
                                            "fancy.shingles"
                                        ],
                                        "boost": 2,
                                        "minimum_should_match": "75%",
                                        "cutoff_frequency": 0.01
                                    }}
                            ],
                            "must": [
                                {
                                    "multi_match": {
                                        "query":  query,
                                        "type":   "most_fields",
                                        "fields": [
                                            "content",
                                            "content.stemmed",
                                            "content.shingles"
                                        ],
                                        "minimum_should_match": "75%",
                                        "cutoff_frequency": 0.01
                                    }}
                            ]
                        }
                    }
                }
            },
            "size": self.RESULTS_PER_PAGE,
            "from": self.RESULTS_PER_PAGE * page,
            "_source": {
                "include": ["title", "url", "meta", "updated_on", "domain"]
            }
        })

    def request_elasticsearch(self, query, page):
        """Return a dict of Elasticsearch results."""
        return self.get_pool().request(
            'GET',
            self.get_endpoint(query, page),
            body=self.get_data(query, page)
        )

    def format_response(self, response):
        res_dict = json.loads(response.data)
        total = res_dict['hits']['total']
        results = [h['_source'] for h in res_dict['hits']['hits']]
        for res in results:
            res['updated_on'] = datetime.strptime(res['updated_on'],
                                                  '%Y-%m-%dT%H:%M:%S')
        return total, results

    def get(self, request, *args, **kwargs):
        kwargs['q'] = request.GET.get('q', '')
        kwargs['page'] = request.GET.get('page', 0)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        query_string = kwargs['q']
        page = kwargs['page']
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
            'page': page+1,
            'max_pages': max_pages,
            'result_begin': self.RESULTS_PER_PAGE * page,
            'result_end': self.RESULTS_PER_PAGE * (page + 1),
            'total_search_results': length,
            'query_string': query_string,
            'search_results': results,
            'search_time': search_time,
            'now': date.fromtimestamp(time.time())
        }

class IipResultsView(TorResultsView):
    def get_endpoint(self, query, page):
        return '/crawl/i2p/_search/?size=100&q=' + query
