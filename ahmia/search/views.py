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
from ahmia.models import SearchResultsClick, SearchQuery, PagePopScore
from ahmia.utils import get_elasticsearch_i2p_index
from ahmia.validators import is_valid_onion_url
from ahmia.views import ElasticsearchBaseListView

logger = logging.getLogger("search")


def onion_redirect(request):
    """Add clicked information and redirect to .onion address."""

    redirect_url = request.GET.get('redirect_url', '')
    search_term = request.GET.get('search_term', '')

    if not redirect_url or not search_term:
        answer = "Bad request: no GET parameter URL."
        return HttpResponseBadRequest(answer)
    try:
        onion = redirect_url.split("://")[1].split(".onion")[0]
        # if len(onion) != 16:
        #     raise ValueError('Invalid onion value = %s' % onion)
        onion = "http://{}.onion/".format(onion)
        if is_valid_onion_url(onion):
            # currently we can't log i2p clicks due to
            # SearchResultsClick.onion_domain having an onion validator
            # Also we don't have yet i2p results in order to test it
            SearchResultsClick.objects.add_or_increment(
                onion_domain=onion,
                clicked=redirect_url,
                search_term=search_term)
    except Exception as error:
        logger.error("Error with redirect URL: {0}\n{1}".format(
            redirect_url, error))

    message = "Redirecting to hidden service."
    return redirect_page(message, 0, redirect_url)


def redirect_page(message, red_time, url):
    """Build and return redirect page."""

    template = loader.get_template('redirect.html')
    content = {'message': message, 'time': red_time, 'redirect': url}
    return HttpResponse(template.render(content))


def filter_hits_by_time(hits, pastdays):
    """Return only the hits that were crawled the past pastdays"""

    time_threshold = datetime.fromtimestamp(
        time.time()) - timedelta(days=pastdays)
    ret = [hit for hit in hits if hit['updated_on'] >= time_threshold]
    return ret


def heuristic_score(ir_score, pp_score):
    """
    A formula to combine IR score given by Elasticsearch and
    PagePop score given by page popularity algorithm. Adjust the
    influence of pr/ir scores according to the number of terms that
    query is consisted of, as well as other factors. Arithmetics is
    black art, it can only improve via manually testing queries, and
    user feedback. Currently its a simple weighted sum.
    todo: improve it
    Normally the more tokens in query the lower pagepop influence
    should be. However the more tokens given the more ES seems to
    diverge IR score. Thus we bypass 'number of tokens' for the moment

    :param ir_score: Information Relevance score by Elasticsearch
    :param pp_score: PagePop score for that domain
    :return: final score
    :rtype: ``float``
    """

    pp_coeff = 0.35
    ir_coeff = 1 - pp_coeff
    ret = pp_score * pp_coeff + ir_score * ir_coeff

    # drag down the average score when the two scores diverge too much
    # pp = pp_coeff * pp_score
    # ir = ir_coeff * ir_score
    # ret = pp * ir / (pp + ir)  # too much of a penalty

    return ret


class TorResultsView(ElasticsearchBaseListView):
    """ Search results view """

    http_method_names = ['get']
    template_name = "tor_results.html"
    RESULTS_PER_PAGE = 100
    object_list = None

    def get_es_context(self, **kwargs):
        return {
            "index": utils.get_elasticsearch_tor_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": kwargs['q'],
                                    "type": "most_fields",
                                    "fields": [
                                        'title^6',
                                        'anchor^6',
                                        'fancy.shingles^3',
                                        'fancy.stemmed^3',
                                        'fancy^3',
                                        'content^1',
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

    def suggest(self, **kwargs):
        """ Did you mean functionality """
        suggest = None
        es_obj = self.es_obj or utils.get_elasticsearch_object()

        payload = {
            "index": utils.get_elasticsearch_tor_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "size": 0,
            "body": {
                "suggest": {
                    "text": kwargs.get('q'),
                    "simple-phrase": {
                        "phrase": {
                            "field": "fancy",
                            "gram_size": 2   # todo make this applicable?
                        }
                    }
                }
            }
        }
        resp = es_obj.search(**payload)

        try:
            suggestions = resp['suggest']['simple-phrase'][0]['options']
            if len(suggestions) > 0:
                suggest = suggestions[0]['text']
        except (TypeError, ValueError) as e:
            logger.exception(e)

        return suggest

    def format_hits(self, hits):
        """
        Transform ES response into a list of results.
        Returns (total number of results, results)
        """
        hits = hits['aggregations']['domains']
        total = len(hits['buckets']) + hits['sum_other_doc_count']

        results = []
        for h in hits['buckets']:
            # replace score, updated_on, anchors with clear values
            tmp = h['score']['hits']['hits'][0]
            res = tmp['_source'].copy()
            res['score'] = tmp['sort'][1] * tmp['sort'][0]
            res['updated_on'] = datetime.strptime(res['updated_on'],
                                                  '%Y-%m-%dT%H:%M:%S')
            try:
                res['anchors'] = res['anchors'][0]
            except (KeyError, TypeError):
                pass

            results.append(res)

        return total, results

    @staticmethod
    def log_stats(**kwargs):
        """log the query for stats calculations"""
        SearchQuery.objects.add_or_increment(
            search_term=kwargs['q'], network='T')

    def sort_results(self):
        """
        Combine IR (Information Relevant) score given by Elasticsearch,
        with PP (Page Popularity) score, to sort the results
        """
        hits = self.object_list[1]  # object_list is tuple(int, list)
        if not hits:
            return

        ir_scores = [h.get('score', 0) for h in hits]
        pp_scores = [PagePopScore.objects.get_score(onion=h['domain'])
                     for h in hits]
        ir_scores_norm = utils.normalize_on_max(ir_scores)
        pp_scores_norm = utils.normalize_on_max(pp_scores)
        # assert len(ir_scores_norm) == len(pp_scores_norm) == len(hits)

        for h, ir, pp in zip(hits, ir_scores_norm, pp_scores_norm):
            h['final_score'] = heuristic_score(ir, pp)

        self.object_list[1] = sorted(
            hits,
            key=lambda k: k['final_score'],
            reverse=True)

    def get(self, request, *args, **kwargs):
        """
        This method is override to add parameters to the get_context_data call
        """
        start = time.time()
        kwargs['q'] = request.GET.get('q', '')
        kwargs['page'] = request.GET.get('page', 0)

        self.log_stats(**kwargs)

        self.object_list = self.get_queryset(**kwargs)

        suggest = self.suggest(**kwargs)
        if suggest != kwargs['q']:
            # if ES fuzziness suggests something else, display it
            kwargs['suggest'] = suggest

        if 'r' in request.GET:  # enable PagePop
            self.sort_results()

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
            'suggest': kwargs.get('suggest'),
            'page': page + 1,
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
            pastdays = int(url_params.get('d'))
        except (TypeError, ValueError):
            # Either pastdays not exists or not valid int (e.g 'all')
            # In any case hits returned without filtering
            pass
        else:
            hits = filter_hits_by_time(hits, pastdays)

        return hits

    def get_queryset(self, **kwargs):
        _, hits = super(TorResultsView, self).get_queryset(**kwargs)
        hits = self.filter_hits(hits)
        return [len(hits), hits]


class IipResultsView(TorResultsView):
    """ I2P Search results view """
    template_name = "i2p_results.html"

    @staticmethod
    def log_stats(**kwargs):
        """Invoked by super().get() to log the query for stats calculations"""
        SearchQuery.objects.add_or_increment(
            search_term=kwargs['q'], network='I')

    def get_es_context(self, **kwargs):
        context = super(IipResultsView, self).get_es_context(**kwargs)
        context['index'] = get_elasticsearch_i2p_index()
        return context
