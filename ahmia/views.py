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
    verify_certs=settings.VERIFY_CERT,
    ssl_show_warn=settings.VERIFY_CERT,
    timeout=settings.ELASTICSEARCH_TIMEOUT
)

SECRET_SALT = settings.SALT

def generate_token(minute=None):
    """Return a 6-char rolling token that changes every minute."""
    if minute is None:
        minute = int(time.time() // 60)
    raw = f"{SECRET_SALT}:{minute}"
    digest = hashlib.sha1(raw.encode()).hexdigest()
    return digest[:6]

def rotating_field_names():
    """Return a 6-char rolling field names for 60 minutes."""
    field_names_60 = []
    now_minute = int(time.time() // 60)
    for i in range(0, 60):  # current + previous 60 minutes
        minute = now_minute - i
        raw = f"{SECRET_SALT}:{minute}"
        digest = hashlib.sha1(raw.encode()).hexdigest()[6:12]
        field_names_60.append(digest)
    return field_names_60

def valid_token(token):
    """Check if token matches any of the last 60 minutes."""
    now_minute = int(time.time() // 60)
    for i in range(0, 60):  # current + previous 60 minutes
        if token == generate_token(now_minute - i):
            return True
    return False

class TokenMixin:
    """Injects a rolling search_token into the context for templates with a search form."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_token"] = generate_token()
        context["token_field"] = rotating_field_names()[0]
        return context

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

class HomepageView(TokenMixin, TemplateView):
    """ Main page view """
    template_name = "index_tor.html"

class PrivacyView(TokenMixin, TemplateView):
    """ Privacy Policy """
    template_name = "privacy.html"

class TermsView(TokenMixin, TemplateView):
    """ Terms of Service """
    template_name = "terms.html"

class LegalView(TokenMixin, TemplateView):
    """ Legal page view """
    template_name = "legal.html"

class DocumentationView(TokenMixin, TemplateView):
    """  Documentation view """
    template_name = "documentation.html"

class IndexingDocumentationView(TokenMixin, TemplateView):
    """Static page about the indexing and crawling."""
    template_name = "indexing.html"

class AboutView(TokenMixin, TemplateView):
    """ About page view """
    template_name = "about.html"

class AddView(TokenMixin, FormView):
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

class AddListView(TokenMixin, ListView):
    """List all added onion addresses view."""
    model = HiddenWebsite
    template_name = "add_list.html"
    context_object_name = "hidden_websites"

    def get_queryset(self):
        """ Retrieve the original queryset and filter it based on banned domains """
        queryset = super().get_queryset()
        banned = banned_domains_db()
        urls = [w for w in queryset if not any(domain in w.onion for domain in banned)]
        domains = list({f"http://{url.onion.split('/')[2]}/" for url in urls})
        return domains

class BlacklistView(TokenMixin, TemplateView):
    """Blacklist page"""
    template_name = "blacklist.html"

class ElasticsearchBaseListView(TokenMixin, ListView):
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
                            "size": 300000  # Adjust based on expected count
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
    main_domain = extract_domain_from_url(redirect_url)
    if not main_domain in settings.HELP_DOMAINS:
        if main_domain in banned_domains_db():
            return HttpResponseBadRequest("Bad request: banned.")
    return HttpResponseRedirect(redirect_url)

def help_page(query):
    """ Return Help page """
    allowed = [45, 95] + list(range(48, 58)) + list(range(97, 123))
    query = ''.join([i if ord(i) in allowed else '_' for i in query.lower()])
    tests = [
        {
            "test": "0", # 0. Neutral message
            "title_en": "ReDirection | Self-Help Program",
            "paragraph_en_1": "ReDirection is a self-help program which aims to help you stop viewing sexual images of children.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Programa de Autoayuda",
            "paragraph_es_1": "ReDirección es un programa de autoayuda, cuyo objetivo es ayudarte a dejar de ver imágenes sexuales de niños/as.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        {
            "test": "1", # 1. Legality/Consequences | Negative-Framed
            "title_en": "ReDirection | Child sexual abuse imagery is illegal.",
            "paragraph_en_1": "Accessing sexual images of children puts you at risk of arrest and may cost you your relationships, your job, or your freedom.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Las imágenes de abuso sexual infantil son ilegales.",
            "paragraph_es_1": "Acceder a imágenes sexuales de niños/as te expone a ser arrestado y puede costarte tus relaciones, tu trabajo o tu libertad.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "2", # 2. Legality/Consequences | Positive-Framed
            "title_en": "ReDirection | Child sexual abuse imagery is illegal.",
            "paragraph_en_1": "Getting professional help may reduce the risk of arrest and help you keep your relationships, your job, your freedom.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Las imágenes de abuso sexual infantil son ilegales.",
            "paragraph_es_1": "Recibir ayuda profesional puede reducir el riesgo de arresto y ayudarte a proteger tus relaciones, tu empleo y tu libertad.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "3", # 3. Harm | Negative-Framed
            "title_en": "ReDirection | Child sexual abuse imagery causes harm to children.",
            "paragraph_en_1": "Searching for and viewing sexual images of children adds to that harm.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Las imágenes de abuso sexual infantil causan daño a los niños y las niñas.",
            "paragraph_es_1": "Buscar y ver estas imágenes sexuales de niños/as aumenta ese daño.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "4", # 4. Harm | Positive-Framed
            "title_en": "ReDirection | Child sexual abuse imagery causes harm to children.",
            "paragraph_en_1": "Getting help to stop viewing sexual images of children is one way you can stop that cycle of harm.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Las imágenes de abuso sexual infantil causan daño a los niños.",
            "paragraph_es_1": "Recibir ayuda para dejar de ver imágenes sexuales de niños/as es una forma de detener ese ciclo de daño.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "5", # 5. Control | Negative-Framed
            "title_en": "ReDirection | Getting help for child sexual abuse imagery starts with a single click.",
            "paragraph_en_1": "Don’t dwell on the barriers stopping you from getting anonymous help.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Recibir ayuda para el consumo de imágenes de abuso sexual infantil comienza con un solo clic.",
            "paragraph_es_1": "No te detengas en las barreras que te impiden obtener ayuda de manera anónima.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "6", # 6. Control | Positive-Framed
            "title_en": "ReDirection | Getting help for child sexual abuse imagery starts with a single click.",
            "paragraph_en_1": "It’s easier than you think to get anonymous help to stop viewing sexual images of children.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Recibir ayuda para el consumo de imágenes de abuso sexual infantil comienza con un solo clic.",
            "paragraph_es_1": "Obtener ayuda anónima para dejar de ver imágenes sexuales de niños/as es más fácil de lo que piensas.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "7", # 7. Distress | Negative-Framed
            "title_en": "ReDirection | How is searching for child sexual abuse imagery affecting you?",
            "paragraph_en_1": "Take a moment to think about how searching for sexual images of children is likely to cause you feelings of shame, guilt, and anxiety.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | ¿Cómo te está afectando buscar imágenes de abuso sexual infantil?",
            "paragraph_es_1": "Tómate un momento para pensar en cómo buscar imágenes sexuales de niños/as probablemente te cause sentimientos de vergüenza, culpa y ansiedad.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "8", # 8. Distress | Positive-Framed
            "title_en": "ReDirection | How is searching for child sexual abuse imagery affecting you?",
            "paragraph_en_1": "Getting help to stop searching for sexual images of children can take away your feelings of shame, guilt, and anxiety.",
            "paragraph_en_2": "You can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | ¿Cómo te está afectando buscar imágenes de abuso sexual infantil?",
            "paragraph_es_1": "Recibir ayuda para dejar de buscar imágenes sexuales de niños/as puede eliminar tus sentimientos de vergüenza, culpa y ansiedad.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        # Random day
        {
            "test": "random" # Triggers random view on selected day
        }
        # DO NOT ADD ANYTHING AFTER THE RANDOM PLACEHOLDER ITEM
    ]
    # Daily rolling index across all items
    anchor = date(2025, 9, 1) # Start day
    days_since_anchor = (date.today() - anchor).days
    if days_since_anchor >= 0: # Start the display on 9 September 2025
        index = days_since_anchor % len(tests)
    else:
        index = 0 # Else, 0, neutral view
    selected_version = tests[index]
    # If today is the 'random' day (triggered by placeholder)
    if selected_version.get("test", "") == "random":
        selected_version = tests[round(time.time()) % (len(tests) - 1)]
    content = {"test_text": selected_version, "query": {"query": query}}
    content["search_token"] = generate_token() # inject token for hidden field
    content["token_field"] = rotating_field_names()[0]
    template = loader.get_template('help.html')
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
        token = ""
        for field_name in rotating_field_names():
            token = request.GET.get(field_name, "")
            if token:
                break
        if not valid_token(token):
            return redirect("home")

        search_term = request.GET.get('q', '')
        if len(search_term) > 100 or len(search_term.split(" ")) > 10:
            answer = "Bad request: too long search query"
            return HttpResponseBadRequest(answer)
        if self.banned_search(search_term):
            return help_page(search_term)
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
            'search_token': generate_token(),
            'token_field': rotating_field_names()[0],
            'max_pages': max_pages,
            'result_begin': self.RESULTS_PER_PAGE * page,
            'result_end': self.RESULTS_PER_PAGE * (page + 1),
            'total_search_results': length,
            'query_string': kwargs['q'],
            'search_results': self.object_list.hits,
            'search_time': kwargs['time'],
            'now': date.fromtimestamp(time.time())
        }
