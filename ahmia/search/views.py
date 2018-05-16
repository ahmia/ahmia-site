"""
Views
Full text search views.
"""
import math
import time
from datetime import date, datetime

from ahmia.views import ElasticsearchBaseListView
from django.http import HttpResponse
from django.template import loader, Context
from ahmia.models import SearchResultsClicks
from ahmia import utils

def onion_redirect(request):
    """Add clicked information and redirect to .onion address."""
    redirect_url = request.GET.get('redirect_url', '')
    search_term = request.GET.get('search_term', '')
    if not redirect_url or not search_term:
        answer = "Bad request: no GET parameter URL."
        return HttpResponseBadRequest(answer)
    try:
        onion = redirect_url.split("://")[1].split(".onion")[0]
        if len(onion) != 16:
            raise ValueError('Invalid onion value = %s' % onion)
        onion = "http://" + onion + ".onion/"
        #clicks, created = SearchResultsClicks.objects.get_or_create(onionDomain=onion, clicked=redirect_url, searchTerm=search_term)
    except Exception as error:
        print( "Error with redirect URL: " + redirect_url )
        print( error )
    message = "Redirecting to hidden service."
    return redirect_page(message, 0, redirect_url)

def redirect_page(message, time, url):
    """Build and return redirect page."""
    template = loader.get_template('redirect.html')
    content = Context( {'message': message, 'time': time, 'redirect': url} )
    return HttpResponse(template.render(content))

class TorResultsView(ElasticsearchBaseListView):
    """ Search results view """
    http_method_names = ['get']
    template_name = "tor_results.html"
    RESULTS_PER_PAGE = 100
    object_list = None

    def get_es_context(self, **kwargs):
        query = kwargs['q']
        return {
            "index": utils.get_elasticsearch_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "type":   "most_fields",
                                    "fields": [
                                        "fancy",
                                        "fancy.stemmed",
                                        "fancy.shingles"
                                    ],
                                    "minimum_should_match": "75%",
                                    "cutoff_frequency": 0.01
                                }
                            }
                        ],
                        "must_not": [
                            {
                                "exists": {
                                    "field": "is_fake",
                                    "field": "is_banned"
                                }
                            }
                        ]
                        # "filter": [
                        #     {
                        #         "missing": {
                        #             "field": "is_fake"
                        #         }
                        #     },
                        #     {
                        #         "missing": {
                        #             "field": "is_banned"
                        #         }
                        #     }
                        # ]
                    }

                },
                "aggregations" : {
                    "domains" : {
                        "terms" : {
                            "size" : 1000,
                            "field" : "domain",
                            "order": {"max_score": "desc"}
                        },
                        "aggregations": {
                            "score": {
                                "top_hits": {
                                    "size" : 1,
                                    "sort": [
                                        {
                                            "authority": {
                                                "order": "desc",
                                                "missing": 0.0000000001
                                            }
                                        },
                                        {
                                            "_score": {
                                                "order": "desc"
                                            }
                                        }
                                    ],
                                    "_source": {
                                        "include": ["title", "url", "meta",
                                                    "updated_on", "domain",
                                                    "authority", "anchors"]
                                    }
                                }
                            },
                            "max_score": {
                                "max": {
                                    "script": "_score"
                                }
                            }
                        }
                    }
                }
            },
            "size": 0
        }

    def format_hits(self, hits):
        """
        Transform ES response into a list of results.
        Returns (total number of results, results)
        """
        hits = hits['aggregations']['domains']
        total = len(hits['buckets']) + hits['sum_other_doc_count']
        results = [h['score']['hits']['hits'][0]['_source']
                   for h in hits['buckets']]
        for res in results:
            try:
                res['anchors'] = res['anchors'][0]
            except KeyError:
                pass
            except TypeError:
                pass
            res['updated_on'] = datetime.strptime(res['updated_on'],
                                                  '%Y-%m-%dT%H:%M:%S')
        return total, results

    def get(self, request, *args, **kwargs):
        """
        This method is override to add parameters to the get_context_data call
        """
        start = time.time()
        kwargs['q'] = request.GET.get('q', '')
        kwargs['page'] = request.GET.get('page', 0)

        self.object_list = self.get_queryset(**kwargs)

        kwargs['time'] = round(time.time() - start, 2)

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """
        Get the context data to render the result page.
        """
        page = kwargs['page']
        length, results = self.object_list
        max_pages = int(math.ceil(float(length) / self.RESULTS_PER_PAGE))

        return {
            'page': page+1,
            'max_pages': max_pages,
            'result_begin': self.RESULTS_PER_PAGE * page,
            'result_end': self.RESULTS_PER_PAGE * (page + 1),
            'total_search_results': length,
            'query_string': kwargs['q'],
            'search_results': results,
            'search_time': kwargs['time'],
            'now': date.fromtimestamp(time.time())
        }

class IipResultsView(TorResultsView):
    """ I2P Search results view """
    template_name = "i2p_results.html"
    def get_es_context(self, **kwargs):
        context = super(IipResultsView, self).get_es_context(**kwargs)
        context['doc_type'] = "i2p"
        return context
