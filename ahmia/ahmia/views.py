"""
Views
Static HTML pages.
These pages does not require database connection.
"""
import hashlib
import logging
from operator import itemgetter

from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from . import utils
from .forms import AddOnionForm, ReportOnionForm
from .models import HiddenWebsite

logger = logging.getLogger("ahmia")


class CoreView(TemplateView):
    """Core page of the website."""
    http_method_names = ['get']


class HomepageView(CoreView):
    """The homepage."""
    template_name = "index_tor.html"


class InvisibleInternetView(CoreView):
    """The main i2p search page."""
    template_name = "index_i2p.html"


class LegalView(CoreView):
    """Static legal page."""
    template_name = "legal.html"


class DocumentationView(CoreView):
    """Static documentation page."""
    template_name = "documentation.html"


class IndexingDocumentationView(CoreView):
    """Static page about the indexing and crawling."""
    template_name = "indexing.html"


class DescPropDocumentationView(CoreView):
    """Static description proposal."""
    template_name = "descriptionProposal.html"


class CreateDescDocumentationView(CoreView):
    """Page to create hidden website description."""
    template_name = "createHsDescription.html"


class AboutView(CoreView):
    """Static about page."""
    template_name = "about.html"


class GsocView(CoreView):
    """Summer of code 2014."""
    template_name = "gsoc.html"


class AddView(FormView):
    """Add form for a new .onion address."""

    form_class = AddOnionForm
    template_name = "add.html"
    success_url = reverse_lazy("add")
    success_msg = _(""" Your request to add a service was successfully submitted.
                        Thank you for improving Ahmia content. A moderator will
                        add it to the index shortly. """)
    exists_msg = _("The specified onion address already exists in our database.")
    invalid_msg = _("Your request to add a service was invalid.")
    fail_msg = _("Internal Server Error occurred. Please try again later")

    def form_valid(self, form):
        r = super(AddView, self).form_valid(form)

        request = self.request
        onion_url = form.cleaned_data['onion'].strip()

        try:
            # created or retrieve
            _, created = HiddenWebsite.objects.get_or_create(onion=onion_url)
        except IntegrityError as e:
            # should never happen: DB error despite earlier validation
            logger.exception(e)
            messages.error(request, self.fail_msg)
        else:
            if created:
                # newly instance created
                messages.success(request, self.success_msg)
            else:
                # fetched, already existed
                messages.warning(request, self.exists_msg)

        return r

    def form_invalid(self, form):
        r = super(AddView, self).form_valid(form)

        logger.info(self.invalid_msg)
        messages.error(self.request, self.invalid_msg)

        return r


def add_list_view(request):
    """List of onions added"""
    template = loader.get_template('add_list.html')
    sites = HiddenWebsite.objects.all()
    sites = [address.onion for address in sites]
    content = {'sites': sites}
    return HttpResponse(template.render(content))


class BlacklistView(FormView):
    """Blacklist report page"""

    form_class = ReportOnionForm
    success_url = "/blacklist/success/"
    template_name = "blacklist.html"

    def get_es_context(self, **kwargs):
        return {
            "index": utils.get_elasticsearch_tor_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "size": 0,
            "body": {
                "query": {
                    "constant_score": {
                        "filter": {
                            "term": {
                                "is_banned": 1
                            }
                        }
                    }
                },
                "aggs": {
                    "domains": {
                        "terms": {
                            "field": "domain",
                            "size": 30000
                        }
                    }
                }
            },
            "_source_include": ["title", "url", "meta", "updated_on", "domain", "is_banned"]
        }

    def form_valid(self, form):
        # todo replace with a spam-tolerant report functionality
        form.send_abuse_report()
        return super(BlacklistView, self).form_valid(form)


class BlacklistSuccessView(CoreView):
    """Onion successfully reported."""
    template_name = "blacklist_success.html"


class ElasticsearchBaseListView(ListView):
    """
    Base view to display lists of items coming from ES
    :todo: TemplateView would probably fit better here
    """
    es_obj = None
    object_list = None  # SimpleNamespace instead of list of instances

    def get_es_context(self, **kwargs):
        """ Get parameters list to use with Elasticsearch.search() """
        raise NotImplementedError

    def format_hits(self, hits):
        """ Format dict returned by Elasticsearch.search() """
        return hits

    def get_queryset(self, **kwargs):
        es_obj = self.es_obj or utils.get_elasticsearch_object()
        hits = es_obj.search(**self.get_es_context(**kwargs))
        return self.format_hits(hits)

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset(**kwargs)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class OnionListView(ElasticsearchBaseListView):
    """ Displays a list of .onion domains as a plain text page """
    template_name = "onions.html"

    def format_hits(self, hits):
        """
        Transform ES response into a list of results.
        Returns (total number of results, results)
        """
        hits = [
            {
                'domain': hit['key'],
                'pages': hit['doc_count']
            }
            for hit in hits['aggregations']['domains']['buckets']
        ]

        hits = sorted(hits, key=itemgetter('domain'))
        return hits

    def get_context_data(self, **kwargs):
        return {
            "domains": self.object_list
        }

    def get_es_context(self, **kwargs):
        return {
            "index": utils.get_elasticsearch_tor_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "size": 0,
            "body": {
                "query": {
                    "bool": {
                        "must_not": [
                            {
                                "match": {
                                    "is_banned": "true"
                                }
                            },
                        ]
                    }
                },
                "aggs": {
                    "domains": {
                        "terms": {
                            "field": "domain",
                            "size": 30000
                        }
                    }
                }
            },
            "_source_include": ["title", "url", "meta", "updated_on", "domain", "is_banned"]
        }


class AddressListView(OnionListView):
    """ Displays a list of .onion domains as a web page """
    template_name = "address.html"


class BannedDomainListView(OnionListView):
    """ Displays a list banned .onion domain's md5 as a plain text page """
    template_name = "banned.html"

    def cached_hits(self, hits):
        """ Fetch cached hits and cache new ones """
        cache_file = "banned_domains.txt"
        lines = []
        try:
            with open(cache_file, 'rt') as filehandle:
                lines = filehandle.readlines()
        except IOError:
            print("Cache file %s is not created yet." % cache_file)
        added = False
        for hit in hits:
            domain = hit['domain']
            new_line = "%s\n" % domain
            if not new_line in lines:
                lines.append(new_line)
                added = True
        if added:
            with open(cache_file, 'w') as filehandle:
                filehandle.writelines(lines)
        return [line.replace("\n", "") for line in lines]

    def format_hits(self, hits):
        """
        Transform ES response into a list of results.
        Returns (total number of results, results)
        """
        hits = super(BannedDomainListView, self).format_hits(hits)
        #hits = [hashlib.md5(hit['domain'].encode('utf-8')).hexdigest() for hit in hits]
        # Cache file to maintain the list of banned domains
        hits = self.cached_hits(hits) # Add cached hits and cache new hits
        hits = [hashlib.md5(hit.encode('utf-8')).hexdigest() for hit in hits]
        return sorted(hits)

    def get_es_context(self, **kwargs):
        return {
            "index": utils.get_elasticsearch_tor_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "size": 0,
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "exists": {
                                    "field": "is_banned"
                                }
                            },
                            {
                                "match": {
                                    "is_banned": "true"
                                }
                            },

                        ]
                    }
                },
                "aggs": {
                    "domains": {
                        "terms": {
                            "field": "domain",
                            "size": 30000
                        }
                    }
                }
            },
            "_source_include": ["title", "url", "meta", "updated_on", "domain", "is_banned"]
        }
