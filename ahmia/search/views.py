"""
Views
Full text search views.
"""
import logging
import math
import time
from datetime import date, datetime, timedelta

from django.http import HttpResponse, HttpResponseBadRequest
from django.template import loader

from ahmia import utils
from ahmia.models import SearchResultsClicks
from ahmia.utils import get_elasticsearch_i2p_index
from ahmia.views import ElasticsearchBaseListView

logger = logging.getLogger(__name__)


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
        onion = "http://{}.onion/".format(onion)
        _, _ = SearchResultsClicks.objects.get_or_create(
            onionDomain=onion, clicked=redirect_url, searchTerm=search_term)
    except Exception as error:
        logger.error("Error with redirect URL: {0}\n{1}".format(redirect_url, error))

    message = "Redirecting to hidden service."
    return redirect_page(message, 0, redirect_url)


def redirect_page(message, red_time, url):
    """Build and return redirect page."""

    template = loader.get_template('redirect.html')
    content = {'message': message, 'time': red_time, 'redirect': url}
    return HttpResponse(template.render(content))


def filter_hits_by_time(hits, pastdays):
    """Return only the hits that were crawled the past pastdays"""

    time_threshold = datetime.fromtimestamp(time.time()) - timedelta(days=pastdays)
    ret = [hit for hit in hits if hit['updated_on'] >= time_threshold]
    return ret


class TorResultsView(ElasticsearchBaseListView):
    """ Search results view """

    http_method_names = ['get']
    template_name = "tor_results.html"
    RESULTS_PER_PAGE = 100
    object_list = None

    def get_es_context(self, **kwargs):
        query = kwargs['q']
        return {
            "index": utils.get_elasticsearch_tor_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "type": "most_fields",
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
                                    # todo duplicate key since its defined as python dict
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
                "aggregations": {
                    "domains": {
                        "terms": {
                            "size": 1000,
                            "field": "domain",
                            "order": {"max_score": "desc"}
                        },
                        "aggregations": {
                            "score": {
                                "top_hits": {
                                    "size": 1,
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
            except (KeyError, TypeError):
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

    def filter_hits(self, hits):
        url_params = self.request.GET

        try:
            pastdays = int(url_params.get('pastdays'))
        except (TypeError, ValueError):
            # Either pastdays not exists or not valid int (e.g 'all')
            # In any case hits returned unchanged
            pass
        else:
            hits = filter_hits_by_time(hits, pastdays)

        return hits

    def get_queryset(self, **kwargs):
        _, hits = super(TorResultsView, self).get_queryset(**kwargs)
        hits = self.filter_hits(hits)
        return len(hits), hits


class IipResultsView(TorResultsView):
    """ I2P Search results view """
    template_name = "i2p_results.html"

    def get_es_context(self, **kwargs):
        context = super(IipResultsView, self).get_es_context(**kwargs)
        context['index'] = get_elasticsearch_i2p_index()
        return context
