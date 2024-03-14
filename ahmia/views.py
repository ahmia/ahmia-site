""" Views """
import time
import hashlib
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from operator import itemgetter
from elasticsearch import Elasticsearch

from django.conf import settings
from django.template import loader
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, FormView, ListView
from django.shortcuts import redirect
from django.contrib import messages
from django.db import IntegrityError

from .forms import AddOnionForm
from .models import HiddenWebsite, BannedWebsite
from .validators import allowed_url, extract_domain_from_url

# Initialize Elasticsearch client outside of the view class to reuse the connection
es_client = Elasticsearch(
    hosts=[settings.ELASTICSEARCH_SERVER],
    http_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
    ca_certs=settings.ELASTICSEARCH_CA_CERTS,
    timeout=settings.ELASTICSEARCH_TIMEOUT
)

def banned_domains_db(hits=None):
    """Retrieve or update the list of banned domains from the database."""
    # Retrieve existing banned domains from the database
    banned_list = set(BannedWebsite.objects.all().values_list('onion', flat=True))
    # If hits are provided, add them to the database
    if hits:
        new_domains = set(hits) - banned_list  # Filter out already banned domains
        for domain in new_domains:
            try:
                BannedWebsite.objects.create(onion=domain)
            except IntegrityError:
                # Handle the case where the domain is already in the database
                # This could happen in concurrent environments, or if hits include duplicates
                continue
        return banned_list.union(set(hits)) # Return combined list
    return banned_list

class HomepageView(TemplateView):
    """ Main page view """
    template_name = "index_tor.html"

class LegalView(TemplateView):
    """ Legal page view """
    template_name = "legal.html"

class DocumentationView(TemplateView):
    """  Documentation view """
    template_name = "documentation.html"

class IndexingDocumentationView(TemplateView):
    """Static page about the indexing and crawling."""
    template_name = "indexing.html"

class AboutView(TemplateView):
    """ About page view """
    template_name = "about.html"

class AddView(FormView):
    """Add new onion addresses view."""
    form_class = AddOnionForm
    template_name = "add.html"
    success_url = reverse_lazy("add")

    def form_valid(self, form):
        # Check if the onion URL already exists in the database
        onion_url = form.cleaned_data['onion']
        if HiddenWebsite.objects.filter(onion=onion_url).exists():
            messages.error(self.request, _("This onion address already exists."))
            return redirect("add")
        HiddenWebsite.objects.create(onion=onion_url)
        messages.success(self.request, _("Onion address added successfully."))
        return super().form_valid(form)

class AddListView(ListView):
    """List all added onion addresses view."""
    model = HiddenWebsite
    template_name = "add_list.html"
    context_object_name = "hidden_websites"

    def get_queryset(self):
        """ Retrieve the original queryset and filter it based on banned domains """
        queryset = super().get_queryset()
        banned = banned_domains_db()
        return [w for w in queryset if not any(domain in w.onion for domain in banned)]

class BlacklistView(TemplateView):
    """Blacklist page"""
    template_name = "blacklist.html"

class ElasticsearchBaseListView(ListView):
    """Base view to display lists of items coming from Elasticsearch."""
    object_list = None

    def get_es_context(self, **kwargs):
        """Define Elasticsearch search context. Must be overridden in subclasses."""
        raise NotImplementedError

    def format_hits(self, hits):
        """Format the Elasticsearch search results."""
        return hits

    def get_queryset(self, **kwargs):
        """Perform the search query to Elasticsearch and return formatted hits."""
        hits = es_client.search(**self.get_es_context(**kwargs))
        return self.format_hits(hits)

    def get(self, request, *args, **kwargs):
        """Handle GET requests and inject the search results into the context."""
        self.object_list = self.get_queryset(**kwargs)
        context = self.get_context_data(object_list=self.object_list, **kwargs)
        return self.render_to_response(context)

class OnionListView(ElasticsearchBaseListView):
    """Displays a list of .onion domains as a plain text page."""
    template_name = "onions.html"

    def format_hits(self, hits):
        """Transform Elasticsearch response into a list of .onion domains."""
        buckets = hits['aggregations']['domains']['buckets']
        hits = [{'domain': hit['key'], 'pages': hit['doc_count']} for hit in buckets]
        return sorted(hits, key=itemgetter('domain'))

    def get_es_context(self, **kwargs):
        """Elasticsearch context specifically for fetching .onion domains."""
        return {
            "index": settings.ELASTICSEARCH_INDEX,
            "body": {
                "size": 0,  # We don't need the actual documents, just the aggregation
                "query": {
                    "bool": {
                        "must_not": {
                            "term": {"is_banned": True}
                        }
                    }
                },
                "aggs": {
                    "domains": {
                        "terms": {
                            "field": "domain",
                            "size": 30000  # Adjust based on expected count
                        }
                    }
                }
            }
        }

    def get_context_data(self, **kwargs):
        """Inject the list of .onion domains into the template context."""
        context = super().get_context_data(**kwargs)
        context['domains'] = self.object_list
        return context

class AddressListView(OnionListView):
    """ Displays a list of .onion domains as a web page """
    template_name = "address.html"

class BannedDomainListView(OnionListView):
    """ Displays a list banned .onion domain's md5 as a plain text page """
    template_name = "banned.html"
    content_type = 'text/plain'  # Serve as plain text

    def get_context_data(self, **kwargs):
        """ Banned domains """
        context = super().get_context_data(**kwargs)
        context['domains'] = self.get_banned_domains()
        return context

    def render_to_response(self, context, **response_kwargs):
        """ Combine all banned domains into a single newline-separated string """
        content = '\n'.join(context['domains'])
        return HttpResponse(content, content_type=self.content_type)

    def cache_hits(self, hits):
        """ Fetch cached hits """
        updated_lines = banned_domains_db(hits)
        return updated_lines

    def get_banned_domains(self):
        """ Get banned """
        query = {
                "size": 0,  # We don't need the actual documents, just the aggregation
                "query": {
                    "bool": {
                        "must": {
                            "term": {"is_banned": True}
                        }
                    }
                },
                "aggs": {
                    "domains": {
                        "terms": {
                            "field": "domain",
                            "size": 30000  # Adjust based on expected count
                        }
                    }
                }
            }

        results = es_client.search(index=settings.ELASTICSEARCH_INDEX, body=query)
        domains = [bucket['key'] for bucket in results['aggregations']['domains']['buckets']]
        cached_domains = self.cache_hits(domains)
        return [hashlib.md5(domain.encode('utf-8')).hexdigest() for domain in cached_domains]

def redirect_page(msg, rtime, url):
    """Build and return a redirect page."""
    content = render_to_string('redirect.html', {'message': msg, 'time': rtime, 'redirect': url})
    return HttpResponse(content)

def remove_non_ascii(text):
    """ Remove non-ASCI characters """
    return ''.join([i if ord(i) < 128 else '' for i in text])

def xss_safe(redirect_url):
    """ Validate that redirect URL is cross-site scripting safe """
    url = remove_non_ascii(redirect_url) # Remove special chars
    url = url.strip().replace(" ", "") # Remove empty spaces and newlines
    if not url.startswith('http'):
        return False # URL does not start with http
    # Look javascript or data inside the URL
    if "javascript:" in url or "data:" in url:
        return False
    return True # XSS safe content

def onion_redirect(request):
    """Add clicked information and redirect to .onion address."""
    redirect_url = request.GET.get('redirect_url', '').replace('%22', '')
    redirect_url = redirect_url.replace('%26', '&').replace('%3F', '?')
    search_term = request.GET.get('search_term', '')
    if not redirect_url or not search_term:
        return HttpResponseBadRequest("Bad request: no GET parameter URL.")
    if not xss_safe(redirect_url):
        return HttpResponseBadRequest("Bad request: URL is not safe or allowed.")
    # Verify it's a valid full .onion URL or valid otherwise
    if not allowed_url(redirect_url):
        return HttpResponseBadRequest("Bad request: this is not an onion address.")
    if extract_domain_from_url(redirect_url) in banned_domains_db():
        return HttpResponseBadRequest("Bad request: banned.")
    return HttpResponseRedirect(redirect_url)

def help_page():
    """ Return Help page """
    template = loader.get_template('help.html')
    content = {}
    return HttpResponse(template.render(content))

def filter_hits_by_time(hits, pastdays):
    """Return only the hits that were crawled the past pastdays"""
    time_threshold = datetime.fromtimestamp(
        time.time()) - timedelta(days=pastdays)
    ret = [hit for hit in hits if hit['updated_on'] >= time_threshold]
    return ret

def filter_hits_by_terms(hits):
    """Child abuse filtering"""
    ret = []
    for hit in hits:
        add = True
        for f_term in settings.FILTER_TERMS_AND_SHOW_HELP:
            if f_term.lower() in hit.get('title', '').lower():
                add = False
                break
            if f_term.lower() in hit.get('meta', '').lower():
                add = False
                break
        if add:
            ret.append(hit)
    return ret

def remove_duplicate_urls(hits):
    """Return results with unique URLs."""
    seen_urls = set()
    unique_hits = []
    results_by_domain = {}
    for hit in hits:
        domain = hit.get('domain', None)
        if not domain:
            continue
        results_by_domain[domain] = results_by_domain.get(domain, 0) + 1
        if results_by_domain[domain] > 10:
            continue
        url = hit.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
            unique_hits.append(hit)
    return unique_hits

class TorResultsView(ElasticsearchBaseListView):
    """ Search results view """
    http_method_names = ['get']
    template_name = "tor_results.html"
    RESULTS_PER_PAGE = 100

    def banned_search(self, search_term):
        """
        This algorithm filters banned search terms.
        It is a best efford solution and it is not perfect.
        """
        for f_term in settings.FILTER_TERMS_AND_SHOW_HELP:
            for term in search_term.split(" "):
                term_ascii = ''.join(c for c in term if c.isdigit() or c.isalpha())
                if f_term.lower() == term.lower() or f_term.lower() == term_ascii.lower():
                    return True # Filtered
        return False # Not filtered

    def get(self, request, *args, **kwargs):
        """
        This method is override to add parameters to the get_context_data call
        """
        start = time.time()
        search_term = request.GET.get('q', '')
        if len(search_term) > 100 or len(search_term.split(" ")) > 10:
            answer = "Bad request: too long search query"
            return HttpResponseBadRequest(answer)
        if self.banned_search(search_term):
            return help_page()
        kwargs['q'] = search_term
        kwargs['page'] = request.GET.get('page', 0)

        self.get_queryset(**kwargs)

        self.filter_hits()

        kwargs['time'] = round(time.time() - start, 2)

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_es_context(self, **kwargs):
        return { "index": settings.ELASTICSEARCH_INDEX, "body":
            {
            "size": 5000,  # Specify the number of search hits to return
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": kwargs['q'],
                                "fields": ["title^6", "h1^5", "content^1"],
                                "type": "best_fields",
                                "minimum_should_match": "75%"
                                }
                        }
                    ],
                    "must_not": [
                        {
                            "term": {"is_banned": True}
                        }
                    ]
                }
            },
            "_source": ["title", "url", "meta", "updated_on", "domain"]
        }}

    def format_hits(self, hits):
        """
        Transform ES response into a list of results.
        """
        try:
            suggest = hits['suggest']['simple-phrase'][0]['options'][0]['text']
        except (KeyError, IndexError, TypeError):
            suggest = None
        total = hits['hits']['total']
        new_hits = []
        for hit in hits['hits']['hits']:
            updated_on = hit['_source']['updated_on']
            new_hit = hit['_source']
            new_hit['updated_on'] = datetime.strptime(updated_on, '%Y-%m-%dT%H:%M:%S')
            new_hits.append(new_hit)
        self.object_list = SimpleNamespace(total=total, hits=new_hits, suggest=suggest)

    def filter_hits(self):
        """
        1. Remove results which contain FILTERED TERMS.
            - Extra measure because the text mining filtering has a delay to ban content.
        2. Use time filter if it is available
        3. Remove dupblicate URLs
        """
        url_params = self.request.GET
        hits = self.object_list.hits
        # Remove duplicate URLs
        hits = remove_duplicate_urls(hits)
        self.object_list.total = len(hits)
        self.object_list.hits = hits
        # Simple extra check to remove child abuse
        hits = filter_hits_by_terms(hits)
        self.object_list.total = len(hits)
        self.object_list.hits = hits
        # Time filtering
        try:
            pastdays = int(url_params.get('d'))
        except (TypeError, ValueError):
            # Either pastdays not exists or not valid int (e.g 'all')
            # Either case hits are not altered
            pass
        else:
            hits = filter_hits_by_time(hits, pastdays)
            self.object_list.hits = hits
            self.object_list.total = len(hits)

    def get_context_data(self, **kwargs):
        """
        Get the context data to render the result page.
        """
        page = kwargs['page']
        length = self.object_list.total
        #max_pages = int(math.ceil(float(length) / self.RESULTS_PER_PAGE))
        max_pages = 1

        return {
            'suggest': self.object_list.suggest,
            'page': page + 1,
            'max_pages': max_pages,
            'result_begin': self.RESULTS_PER_PAGE * page,
            'result_end': self.RESULTS_PER_PAGE * (page + 1),
            'total_search_results': length,
            'query_string': kwargs['q'],
            'search_results': self.object_list.hits,
            'search_time': kwargs['time'],
            'now': date.fromtimestamp(time.time())
        }
