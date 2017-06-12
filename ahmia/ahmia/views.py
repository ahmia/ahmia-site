"""

Views
Static HTML pages.
These pages does not require database connection.

"""
from operator import itemgetter
import hashlib
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from ahmia.models import HiddenWebsite
from ahmia import utils
from .forms import AddOnionForm, ReportOnionForm
from django.shortcuts import render, redirect



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

class AddView(TemplateView):
    """Add form for a new .onion address."""
    form_class = AddOnionForm
    template_name = "add.html"

    def post(self, request):
        domain = AddOnionForm()
        if request.method == "POST":
            domain = AddOnionForm(request.POST)
            print domain
            if domain.is_valid():
                onion = request.POST.get('onion','')
                onion = HiddenWebsite(onion = onion)
                onion.save() 
                return redirect('/add/success')

        return render(request,self.template_name)

    def form_valid(self, form):
        form.send_new_onion()
        return super(AddView, self).form_valid(form)


class AddSuccessView(CoreView):
    """Onion successfully added."""
    template_name = "add_success.html"

class AddListView(TemplateView):
    """List of onions added"""
    template_name = "add_list.html"
    def new_onion(self, sites):
        sites = HiddenWebsite.objects.all()
        sites = [address.onion for address in sites]
        return sorted(sites)

class BlacklistView(FormView):
    """Return a blacklist page with MD5 sums of banned content."""
    form_class = ReportOnionForm
    success_url = "/blacklist/success/"
    template_name = "blacklist.html"

    def form_valid(self, form):
        form.send_abuse_report()
        return super(BlacklistView, self).form_valid(form)

class BlacklistSuccessView(CoreView):
    """Onion successfully reported."""
    template_name = "blacklist_success.html"

class ElasticsearchBaseListView(ListView):
    """ Base view to display lists of items coming from ES """
    object_list = None
    es_obj = None

    def get_es_context(self, **kwargs):
        """ Get parameters list to use with Elasticsearch.search() """
        raise NotImplementedError

    def format_hits(self, hits):
        """ Format dict returned by Elasticsearch.search() """
        return hits

    def get_queryset(self, **kwargs):
        if self.es_obj is None:
            es_obj = utils.get_elasticsearch_object()
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
        hits = [{'domain': hit['key'], 'pages': hit['doc_count']}
                for hit in hits['aggregations']['domains']['buckets']]
        hits = sorted(hits, key=itemgetter('domain'))
        return hits

    def get_context_data(self, **kwargs):
        return {
            "domains": self.object_list
        }

    def get_es_context(self, **kwargs):
        return {
            "index": utils.get_elasticsearch_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "size": 0,
            "body": {
                "aggs" : {
                    "domains" : {
                        "terms" : {"field" : "domain",
                                   "size": 10000}
                    }
                }
            },
            "_source_include": ["title", "url", "meta", "updated_on", "domain"]
        }

class AddressListView(OnionListView):
    """ Displays a list of .onion domains as a web page """
    template_name = "address.html"

class BannedDomainListView(OnionListView):
    """ Displays a list banned .onion domain's md5 as a plain text page """
    template_name = "banned.html"

    def format_hits(self, hits):
        """
        Transform ES response into a list of results.
        Returns (total number of results, results)
        """
        hits = super(BannedDomainListView, self).format_hits(hits)
        hits = [hashlib.md5(hit['domain']).hexdigest() for hit in hits]
        return sorted(hits)

    def get_es_context(self, **kwargs):
        return {
            "index": utils.get_elasticsearch_index(),
            "doc_type": utils.get_elasticsearch_type(),
            "size": 0,
            "body": {
                "query": {
                    "constant_score" : {
                        "filter" : {
                            "term" : {
                                "is_banned" : 1
                            }
                        }
                    }
                },
                "aggs" : {
                    "domains" : {
                        "terms" : {"field" : "domain",
                                   "size": 1000}
                    }
                }
            },
            "_source_include": ["title", "url", "meta", "updated_on", "domain"]
        }
