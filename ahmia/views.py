""" Views """
import time
import hashlib
import re
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from operator import itemgetter
from elasticsearch import Elasticsearch

from django.conf import settings
from django.template import loader
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
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

    def get(self, request, *args, **kwargs):
        if request.GET.get("format") == "json":
            return JsonResponse({"services": sorted(self.get_queryset())})
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """ New onions """
        queryset = HiddenWebsite.objects.all().only("onion")
        domains = set() # Extract unique domains efficient
        for onion_url in queryset.values_list("onion", flat=True):
            try:
                domain = onion_url.split("/")[2]
                domains.add(f"http://{domain}/")
            except (IndexError, AttributeError):
                continue
        return list(domains)

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
    category = request.GET.get('category', '')
    if category and category not in settings.FILTER_TERMS_BY_CATEGORY:
        return HttpResponseBadRequest("Bad request: invalid category.")
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

def help_page(query, category):
    """ Return Help page with category-specific messaging. """
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
            "test": "1", # Harm Negative-Framed + Legal Positive-Framed
            "title_en": "ReDirection | Child sexual abuse imagery causes harm to children and is illegal.",
            "paragraph_en_1": "Searching for and viewing sexual images of children harms children and is illegal. Getting professional help may reduce the risk of arrest and help you keep your relationships, your job, and your freedom.",
            "paragraph_en_2": "A single click and you can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Las imágenes de abuso sexual infantil causan daño a los niños y las niñas y son ilegales.",
            "paragraph_es_1": "Buscar y ver imágenes sexuales de niños y niñas causa daño a los menores y es ilegal. Recibir ayuda profesional puede reducir el riesgo de detención y ayudarte a conservar tus relaciones, tu empleo y tu libertad.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "2", # Harm Negative-Framed + Legal Positive-Framed
            "title_en": "ReDirection | Viewing child sexual abuse imagery harms children and puts you at risk.",
            "paragraph_en_1": "Every time sexual images of children are viewed, real children are harmed. This behaviour is illegal, but seeking professional help now may lower the risk of arrest and help protect your future.",
            "paragraph_en_2": "A single click and you can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Ver imágenes de abuso sexual infantil daña a los niños y te pone en riesgo.",
            "paragraph_es_1": "Cada vez que se ven imágenes sexuales de niños y niñas, se causa daño real a menores. Este comportamiento es ilegal, pero recibir ayuda profesional ahora puede reducir el riesgo de detención y ayudarte a proteger tu futuro.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "3", # Harm Negative-Framed + Legal Positive-Framed
            "title_en": "ReDirection | Child sexual abuse imagery causes lasting harm — help can stop it.",
            "paragraph_en_1": "Sexual images of children are created through abuse that causes lifelong harm. This content is illegal, but getting help can reduce the risk of arrest and help you regain control of your life.",
            "paragraph_en_2": "A single click and you can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Las imágenes de abuso sexual infantil causan daños duraderos — la ayuda puede detenerlo.",
            "paragraph_es_1": "Las imágenes sexuales de niños y niñas se producen a través de abusos que causan daños de por vida. Este contenido es ilegal, pero recibir ayuda puede reducir el riesgo de detención y ayudarte a recuperar el control de tu vida.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        {
            "test": "4", # Harm Negative-Framed + Legal Positive-Framed
            "title_en": "ReDirection | Child sexual abuse imagery harms children — getting help protects you.",
            "paragraph_en_1": "Searching for sexual images of children causes serious harm to victims and is illegal. Choosing professional help can reduce the risk of arrest and help you keep what matters most in your life.",
            "paragraph_en_2": "A single click and you can take the first step to change your behaviour by accessing support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Las imágenes de abuso sexual infantil dañan a los niños — recibir ayuda te protege.",
            "paragraph_es_1": "Buscar imágenes sexuales de niños y niñas causa graves daños a las víctimas y es ilegal. Elegir ayuda profesional puede reducir el riesgo de detención y ayudarte a conservar lo que más importa en tu vida.",
            "paragraph_es_2": "Puedes dar el primer paso para cambiar tu comportamiento accediendo a apoyo a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:"
        },
        # Random day
        #{
        #    "test": "random" # Triggers random view on selected day
        #}
        # DO NOT ADD ANYTHING AFTER THE RANDOM PLACEHOLDER ITEM
    ]
    category_messages = {
        "AI_CSAM": {
            "category": "AI_CSAM",
            "title_en": "ReDirection | AI-generated sexual content involving children is not a harmless alternative.",
            "paragraph_en_1": "Searching for or creating sexualised AI-generated depictions of children can reinforce sexual interest in children and harmful patterns of behaviour. Choosing synthetic material does not remove the need to address those patterns.",
            "paragraph_en_2": "You can take the first step toward stopping by accessing confidential support through the ReDirection program.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | El contenido sexual generado por IA que representa a menores no es una alternativa inofensiva.",
            "paragraph_es_1": "Buscar o crear representaciones sexuales de menores generadas por IA puede reforzar el interés sexual en niños y patrones de comportamiento perjudiciales. Elegir material sintético no elimina la necesidad de abordar esos patrones.",
            "paragraph_es_2": "Puedes dar el primer paso para detener este comportamiento accediendo a apoyo confidencial a través del programa ReDirección.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        "COM_groups": {
            "category": "COM_groups",
            "title_en": "ReDirection | Online groups can normalise and reinforce harmful behaviour.",
            "paragraph_en_1": "Communities that share, encourage, or normalise sexual material involving children can make harmful behaviour feel acceptable and harder to stop. Leaving those groups can be an important step toward change.",
            "paragraph_en_2": "Confidential professional support can help you step away from these communities and reduce harmful behaviour.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Los grupos en línea pueden normalizar y reforzar comportamientos perjudiciales.",
            "paragraph_es_1": "Las comunidades que comparten, fomentan o normalizan material sexual relacionado con menores pueden hacer que un comportamiento perjudicial parezca aceptable y sea más difícil de detener. Alejarse de estos grupos puede ser un paso importante hacia el cambio.",
            "paragraph_es_2": "El apoyo profesional confidencial puede ayudarte a alejarte de estas comunidades y reducir conductas perjudiciales.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        "contact_offending_related": {
            "category": "contact_offending_related",
            "title_en": "ReDirection | If you are thinking about sexual contact with a child, seek help before anyone is harmed.",
            "paragraph_en_1": "Do not approach, groom, arrange sexual contact with, or sexually involve a child. If your searches relate to acting on sexual thoughts involving children, this is a point where you can choose not to progress further.",
            "paragraph_en_2": "Confidential professional support can help you manage these thoughts and prevent contact offending.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Si estás pensando en tener contacto sexual con un menor, busca ayuda antes de que alguien resulte dañado.",
            "paragraph_es_1": "No te acerques, captes, organices contacto sexual ni involucres sexualmente a un menor. Si tus búsquedas están relacionadas con actuar sobre pensamientos sexuales que involucran a niños, este es un momento en el que puedes decidir no avanzar más.",
            "paragraph_es_2": "El apoyo profesional confidencial puede ayudarte a manejar estos pensamientos y prevenir delitos sexuales de contacto.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        "CSAM_known_content": {
            "category": "CSAM_known_content",
            "title_en": "ReDirection | Searching for specific child sexual abuse material can become an established pattern.",
            "paragraph_en_1": "Looking for particular victims, series, or named material can indicate an established pattern of seeking child sexual abuse material. Repeated searching continues demand for material created through the abuse and exploitation of children.",
            "paragraph_en_2": "You can interrupt this pattern. Confidential professional support can help you stop searching for and viewing this material.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Buscar material específico de abuso sexual infantil puede convertirse en un patrón establecido.",
            "paragraph_es_1": "Buscar víctimas concretas, series o material conocido puede indicar un patrón establecido de búsqueda de material de abuso sexual infantil. La búsqueda repetida mantiene la demanda de material creado mediante el abuso y la explotación de menores.",
            "paragraph_es_2": "Puedes interrumpir este patrón. El apoyo profesional confidencial puede ayudarte a dejar de buscar y ver este material.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        "CSAM_site_navigation": {
            "category": "CSAM_site_navigation",
            "title_en": "ReDirection | Stop before entering a service that distributes child sexual abuse material.",
            "paragraph_en_1": "Searching for a known service or site that distributes sexual material involving children is a point where you can interrupt the behaviour before continuing to that material.",
            "paragraph_en_2": "Instead of continuing, you can take the first step toward stopping and access confidential professional support.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Detente antes de entrar en un servicio que distribuye material de abuso sexual infantil.",
            "paragraph_es_1": "Buscar un servicio o sitio conocido que distribuye material sexual relacionado con menores es un punto en el que puedes interrumpir el comportamiento antes de continuar hacia ese material.",
            "paragraph_es_2": "En lugar de continuar, puedes dar el primer paso para detenerte y acceder a apoyo profesional confidencial.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        "CSAM_harm_framing": {
            "category": "CSAM_harm_framing",
            "title_en": "ReDirection | Sexual violence against children causes severe and lasting harm.",
            "paragraph_en_1": "Searching for sexual material that emphasises rape, pain, humiliation, coercion, or violence involves the sexualisation of serious harm to children. Do not allow these searches or fantasies to progress toward further harmful behaviour.",
            "paragraph_en_2": "Confidential professional support can help you manage these interests and stop harmful patterns of behaviour.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | La violencia sexual contra menores causa daños graves y duraderos.",
            "paragraph_es_1": "Buscar material sexual que enfatiza violación, dolor, humillación, coacción o violencia implica sexualizar daños graves a menores. No permitas que estas búsquedas o fantasías avancen hacia comportamientos más perjudiciales.",
            "paragraph_es_2": "El apoyo profesional confidencial puede ayudarte a manejar estos intereses y detener patrones de comportamiento perjudiciales.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        "CSAM_affiliative_framing": {
            "category": "CSAM_affiliative_framing",
            "title_en": "ReDirection | Caring about a child means protecting their safety and boundaries.",
            "paragraph_en_1": "Describing sexual interest in children as love does not make sexual behaviour or sexual material involving children safe or reciprocal. Children need adults to maintain protective sexual boundaries.",
            "paragraph_en_2": "If you experience sexual thoughts about children, confidential professional support can help you manage them without harming a child.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Cuidar a un menor significa proteger su seguridad y sus límites.",
            "paragraph_es_1": "Describir el interés sexual por menores como amor no hace que el comportamiento sexual o el material sexual relacionado con niños sea seguro ni recíproco. Los menores necesitan que los adultos mantengan límites sexuales protectores.",
            "paragraph_es_2": "Si tienes pensamientos sexuales sobre menores, el apoyo profesional confidencial puede ayudarte a manejarlos sin causar daño a un niño.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
        "CSAM_general": {
            "category": "CSAM_general",
            "title_en": "ReDirection | You can stop searching for child sexual abuse material.",
            "paragraph_en_1": "Searching for and viewing sexual material involving children contributes to a pattern connected to the abuse and exploitation of children. You can choose to interrupt that pattern now.",
            "paragraph_en_2": "Confidential professional support can help you stop seeking this material and change your behaviour.",
            "paragraph_en_3": "The ReDirection program is accessible in the Tor network:",
            "title_es": "ReDirección | Puedes dejar de buscar material de abuso sexual infantil.",
            "paragraph_es_1": "Buscar y ver material sexual relacionado con menores contribuye a un patrón conectado con el abuso y la explotación de niños. Puedes decidir interrumpir ese patrón ahora.",
            "paragraph_es_2": "El apoyo profesional confidencial puede ayudarte a dejar de buscar este material y cambiar tu comportamiento.",
            "paragraph_es_3": "El programa ReDirección es accesible a través del navegador Tor:",
        },
    }
    # Daily rolling index across all items
    anchor = date(2025, 9, 1) # Start day
    days_since_anchor = (date.today() - anchor).days
    if settings.CATEGORY_INTERVENTION_TEST_ENABLED:
        if days_since_anchor >= 0: # Start the display on 9 September 2025
            index = days_since_anchor % len(tests)
        else:
            index = 0 # Else, 0, neutral view
        selected_version = tests[index]
        # If today is the 'random' day (triggered by placeholder)
        if selected_version.get("test", "") == "random":
            selected_version = tests[round(time.time()) % (len(tests) - 1)]
        selected_version = selected_version.copy()
        selected_version.update(category_messages.get(category, {}))
    else:
        # Before the intervention test is activated, always show one neutral message.
        selected_version = tests[0]
    # Background color rotation logic
    color_sets = [
        #("#0969f6", "#6ba7fa"),  # blue
        ("#f6f609", "#fafa6b"),  # yellow
        ("#f68b09", "#fab96b"),  # orange
        #("#f60909", "#fa6b6b"),  # red
        #("#777777", "#bbbbbb"),  # gray
        #("#09f609", "#6bfa6b"),  # green
    ]
    # Select color for each full test cycle
    color_index = (days_since_anchor // len(tests)) % len(color_sets)
    bg_primary, bg_secondary = color_sets[color_index]

    content = {
        "test_text": selected_version,
        "query": {"query": query},
        "category": (
            category if settings.CATEGORY_INTERVENTION_TEST_ENABLED else ""
        ),
        "bg_primary": bg_primary,
        "bg_secondary": bg_secondary,
        "search_token": generate_token(),
        "token_field": rotating_field_names()[0],
    }
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

    @staticmethod
    def _normalise_query_words(value):
        """Return lowercase alphanumeric words from a query or filter term."""
        return re.findall(r'[^\W_]+', value.lower(), flags=re.UNICODE)

    @classmethod
    def _category_matches_query(cls, search_term, filtered_terms):
        """Return True when any category term occurs as complete query words."""
        query_words = cls._normalise_query_words(search_term.replace('+', ' '))
        if not query_words:
            return False

        for filtered_term in filtered_terms:
            term_words = cls._normalise_query_words(filtered_term.replace('+', ' '))
            if not term_words:
                continue

            width = len(term_words)
            for index in range(0, len(query_words) - width + 1):
                if query_words[index:index + width] == term_words:
                    return True

        return False

    def banned_search(self, search_term):
        """
        Return one primary intervention category for a filtered query.

        If a query matches any non-AI filter category and also contains a
        separate AI modifier word, classify it as AI_CSAM. Otherwise use the
        normal category priority.
        """
        matched_categories = {
            category
            for category in settings.CATEGORY_PRIORITY
            if category != "AI_CSAM"
            and self._category_matches_query(
                search_term, settings.FILTER_TERMS_BY_CATEGORY[category]
            )
        }

        if matched_categories:
            query_words = set(
                self._normalise_query_words(search_term.replace('+', ' '))
            )
            if query_words & {"ai", "generated", "syntetic", "synthetic"}:
                return "AI_CSAM"

        for category in settings.CATEGORY_PRIORITY:
            if category in matched_categories:
                return category

        return None

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
        search_terms = [
            term for term in re.split(r'[+\s]+', search_term) if term
        ]
        if len(search_term) > 100 or len(search_terms) > 10:
            answer = "Bad request: too long search query"
            return HttpResponseBadRequest(answer)
        category = self.banned_search(search_term)
        if category:
            return help_page(search_term, category)
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
