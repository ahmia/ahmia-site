"""

Views
Full text search views.
YaCy back-end connections.

"""
import time
import urllib2  # URL encode

import simplejson as json
import urllib3  # HTTP conncetions
from django.conf import settings  # For the back-end connection settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.template import Context, loader
from django.views.decorators.http import require_GET, require_http_methods
from lxml import etree  # To handle the XML answers from the YaCy

import ahmia.view_help_functions as helpers  # My view_help_functions.py
from ahmia.models import HiddenWebsite, HiddenWebsitePopularity
from haystack.query import SearchQuerySet

@require_http_methods(["GET", "POST"])
def proxy(request):
    """Proxy connection to """
    full_url = request.get_full_path()
    http = urllib3.PoolManager()
    url = settings.PROXY_BASE_URL + full_url.replace("/elasticsearch/", "")
    content_type = {'Content-Type':request.META.get('CONTENT_TYPE')}
    response = http.request(request.method, url, headers=content_type, body=request.body)
    r_type = response.getheader('content-type')
    r_data = response.data
    r_status = response.status
    return HttpResponse(content=r_data, content_type=r_type, status=r_status)

@require_GET
def solrapi(request):
    """Solr API to search domain. Returns a list of domains."""
    query = request.GET.get('q', '')
    domain_list = []
    # Query format is key=value
    # /search/API?q=key=value
    # Examples: title=alert, server_header=openresty, text=ahmia, h1=Hidden Service, h2=Hidden Service
    # Query key=value must be shorter than 120 chars
    if query and "=" in query and len(query) < 120 and len(query.split("=")) == 2:
        query = query.split("=")
        key =  query[0]
        value = query[1].replace(" ", "+")
        http = urllib3.PoolManager()
        url = settings.SOLR_ADDRESS + "/select/?q=" + key + "%3A" + value + "&fl=domain"
        url = url + '&start=0&rows=200&indent=on&group.field=domain&wt=python&group=true&group.limit=100'
        response = http.request('GET', url)
        # If Solr answer is 200 OK then build a domain list
        if response.status == 200:
            obj_data = eval(response.data) # Answer string to object
            groups = obj_data["grouped"]["domain"]["groups"]
            for group in groups:
                domains = group["doclist"]["docs"]
                for domain in domains:
                    domain_str = domain["domain"]
                    if 28 < len(domain_str) < 32: # Seems to be onion domain
                        domain_list.append(domain_str+"\n")
        domain_list = sorted(set(domain_list)) # Sort the domains
    return StreamingHttpResponse(domain_list, content_type="text/plain")

@require_GET
def autocomplete(request):
    """Autocomplete function to full text Haystack based search."""
    sqs = SearchQuerySet().autocomplete(text=request.GET.get('q', ''))[:5]
    suggestions = [result.title for result in sqs]
    # Make sure you return a JSON object, not a bare list.
    # Otherwise, you could be vulnerable to an XSS attack.
    the_data = json.dumps({
        'results': suggestions
    })
    return HttpResponse(the_data, content_type='application/json')

@require_GET
def default(request):
    """The default page."""
    return redirect('/search/')

@require_GET
def search_page(request):
    """The default full text search page."""
    query_string = request.GET.get('q', '')
    search_time = ""
    if query_string:
        start = time.time()
        if ".onion" in request.get_host():
            show_tor2web_links = False
        else:
            show_tor2web_links = True
        search_results = query(query_string, show_tor2web_links)
        end = time.time()
        search_time = end - start
        search_time = round(search_time, 2)
    else:
        search_results = ""
    onions = HiddenWebsite.objects.all()
    template = loader.get_template('full_text_search.html')
    content = Context({'search_results': search_results,
        'search_time': search_time,
        'count_banned': onions.filter(banned=True, online=True).count(),
        'count_online': onions.filter(banned=False, online=True).count()})
    return HttpResponse(template.render(content))

@require_GET
def yacy_connection(request, query_string):
    """Direct YaCy search wrapper."""
    url = request.get_full_path()
    if url == "/yacysearch.html":
        url = ""
    http = urllib3.PoolManager()
    url = settings.YACY[:-1] + url
    response = http.request('GET', url)
    r_type = response.getheader('content-type')
    r_data = response.data
    r_status = response.status
    return HttpResponse(content=r_data, content_type=r_type, status=r_status)

@require_GET
def yacy_static(request, query_string):
    url = request.get_full_path()
    return redirect('/static/yacy'+url)

@require_GET
def find(request, query_string):
    """XSLT based search view. For special use."""
    if not query_string and 's' in request.GET:
        query_string = request.GET.get('s')
    xml = str(get_query(query_string))
    xml = xml.replace("/yacysearch.xsl", "/static/xslt/yacysearch.xsl")
    xml = xml.replace("<rss", "<lol")
    xml = xml.replace("</rss>", "</lol>")
    return HttpResponse(xml, content_type="application/xml")

def get_query(query_string):
    """Wrapper to YaCy installation."""
    #<yacy_host>/yacysearch.rss?query=<search_string>&size=<max_hits>
    try:
        query_string = urllib2.quote(query_string.encode("utf8"))
        url = settings.YACY + "yacysearch.rss?query=" + query_string
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        data = response.data
        return data
    except Exception as error:
        print error

def query(query_string, show_tor2web_links=True):
    """Build HTML answer from the answer of the YaCy back-end."""
    try:
        xml = get_query(query_string)
        root = etree.fromstring(xml)
        html_answer = build_html_answer(root, show_tor2web_links)
        if not html_answer:
            html_answer = '<li class="hs_site"><h3>No search results</h3></li>'
        return html_answer
    except Exception as error:
        print error
        return '<li class="hs_site"><h3>No search results</h3></li>'

def build_html_answer(root, show_tor2web_links):
    """Builds HTML answer from the XML."""
    results = []
    for element in root.iter("item"):
        link = element.find("link").text or ""
        # HTML escape the link (href attribute)
        link = helpers.html_escape(link)
        # Show link on title if there is no title
        title = element.find("title").text or link
        redirect_link = "/redirect?redirect_url=" + link
        description = element.find("description").text or ""
        pub_date = element.find("pubDate").text or ""
        answer = '<h3><a href="' + link + '">' + title + '</a></h3>'
        answer = answer + '<div class="infotext"><p class="links">'
        answer = answer + 'Direct link: <a href="' + redirect_link + '">'
        answer = answer + link + '</a></p>'
        if show_tor2web_links:
            tor2web_link = link.replace('.onion/', '.tor2web.fi/')
            redirect_tor2web_link = "/redirect?redirect_url=" + tor2web_link
            answer = answer + '<p class="links"> Access without Tor Browser: '
            answer = answer + '<a href="'
            answer = answer + redirect_tor2web_link + '">' + tor2web_link
            answer = answer + '</a></p>'
        answer = answer + description
        answer = answer + '<p class="urlinfo">' + pub_date + '</p></div>'
        answer = '<li class="hs_site">' + answer + '</li>'
        # Calculate the place of the result
        namespaces = {'yacy': 'http://www.yacy.net/'}
        host = element.find("yacy:host", namespaces=namespaces).text or ""
        add_result(answer, host, results)
    html_answer = sort_results(results)
    return html_answer

def add_result(answer, host, results):
    """Add new search result and get the stats about it."""
    if host:
        onion_id = host.replace(".onion", "")
        tor2web, backlinks, clicks = get_popularity(onion_id)
        if tor2web > 0 or backlinks > 0 or clicks > 0:
            results.append(Popularity(host, answer, tor2web, backlinks, clicks))
    else:
        results.append(Popularity(host, answer, 1, 1, 1))

def get_popularity(onion):
    """Calculate the popularity of an onion page."""
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except ObjectDoesNotExist:
        return 1, 1, 1
    if hs.banned:
        return 0, 0, 0
    try:
        pop = HiddenWebsitePopularity.objects.get(about=hs)
        clicks = pop.clicks
        public_backlinks = pop.public_backlinks
        tor2web = pop.tor2web
        return tor2web, public_backlinks, clicks
    except ObjectDoesNotExist:
        return 1, 1, 1

def sort_results(p_tuples):
    """Sort the results according to stats."""
    # Scaling the number of backlinks
    p_by_backlinks = sorted(p_tuples, key=lambda popularity: popularity.backlinks, reverse=True)
    for index, p_info in enumerate(p_by_backlinks):
        p_info.backlinks = 1 / (float(index) + 1)
    # Scaling the number of clicks
    p_by_clicks = sorted(p_by_backlinks, key=lambda popularity: popularity.clicks, reverse=True)
    for index, p_info in enumerate(p_by_clicks):
        p_info.clicks = 1 / (float(index) + 1)
    # Scaling the number of Tor2web
    p_by_tor2web = sorted(p_by_clicks, key=lambda popularity: popularity.tor2web, reverse=True)
    for index, p_info in enumerate(p_by_tor2web):
        p_info.tor2web = 1 / (float(index) + 1)
    p_by_sum = sorted(p_by_tor2web, key=lambda popularity: popularity.sum(), reverse=True)
    html_answer = ""
    for p_info in p_by_sum:
        html_answer = html_answer + p_info.content
    return html_answer

class Popularity(object):
    """Popularity by Tor2web visits, backlinks and clicks."""
    def __init__(self, url, content, tor2web, backlinks, clicks):
        self.url = url
        self.content = content
        self.tor2web = float(tor2web)
        self.backlinks = float(backlinks)
        self.clicks = float(clicks)
    def func(self):
        """Print the sum function."""
        print "2.0*%f + 3.0*%f + 1.0*%f" % self.tor2web, self.backlinks, self.clicks
    def sum(self):
        """Calculate the popularity."""
        #The model can be very simple (sum)
        #What are the proper coefficients?
        sum_function = 2.0*self.tor2web + 3.0*self.backlinks + 1.0*self.clicks
        return sum_function
    def __repr__(self):
        return repr((self.url, self.tor2web, self.backlinks, self.clicks, self.sum))
