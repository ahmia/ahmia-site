"""

Views
Full text search views.
YaCy back-end connections.

"""
import urllib2 # URL encode
import urllib3 # HTTP conncetions
from lxml import etree # To handle the XML answers from the YaCy
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.conf import settings # For the back-end connection settings
from ahmia.models import HiddenWebsite
from django.template import Context, loader

def default(request):
    """The default page."""
    if request.method == 'GET':
        return redirect('/search/')
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def search_page(request):
    """The default full text search page."""
    query_string = request.GET.get('q', '')
    if query_string:
        search_results = query(query_string)
    else:
        search_results = ""
    onions = HiddenWebsite.objects.all()
    template = loader.get_template('full_text_search.html')
    content = Context({'search_results': search_results,
        'count_banned': onions.filter(banned=True).count(),
        'count_online': onions.filter(banned=False, online=True).count()})
    return HttpResponse(template.render(content))

def yacy_connection(request, query_string):
    """Direct YaCy search wrapper."""
    if request.method == 'GET':
        http = urllib3.PoolManager()
        query_string = urllib2.quote(query_string.encode("utf8"))
        url = settings.YACY + query_string
        response = http.request('GET', url)
        if response.status is not 200:
            return HttpResponseBadRequest("Bad request")
        r_type = response.getheader('content-type')
        data = response.data
        if "text" in r_type or "javascript" in r_type:
            data = data.replace('/suggest.json', '/yacy/suggest.json')
            data = data.replace('href="/', 'href="/yacy/')
            data = data.replace('src="/', 'scr="/yacy/')
            data = data.replace("href='/", "href='/yacy/")
            data = data.replace("src='/", "scr='/yacy/")
        return HttpResponse(data, content_type=r_type)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def find(request, query_string):
    """XSLT based search view. For special use."""
    if request.method == 'GET':
        if not query_string and 's' in request.GET:
            query_string = request.GET.get('s')
        xml = str(get_query(query_string))
        xml = xml.replace("/yacysearch.xsl", "/static/xslt/yacysearch.xsl")
        xml = xml.replace("<rss", "<lol")
        xml = xml.replace("</rss>", "</lol>")
        return HttpResponse(xml, content_type="application/xml")
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

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

def html_escape(text):
    """Produce entities within text."""
    html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;"
    }
    return "".join(html_escape_table.get(c, c) for c in text)

def query(query_string):
    """Build HTML answer from the answer of the YaCy back-end."""
    try:
        xml = get_query(query_string)
        root = etree.fromstring(xml)
        html_answer = ""
        for element in root.iter("item"):
            link = element.find("link").text or ""
            # HTML escape the link (href attribute)
            link = html_escape(link)
            # Show link on title if there is no title
            title = element.find("title").text or link
            redirect_link = "/redirect?redirect_url=" + link
            tor2web_link = link.replace('.onion/', '.tor2web.fi/')
            redirect_tor2web_link = "/redirect?redirect_url=" + tor2web_link
            description = element.find("description").text or ""
            pub_date = element.find("pubDate").text or ""
            answer = '<h3><a href="' + link + '">' + title + '</a></h3>'
            answer = answer + '<div class="infotext"><p class="links">'
            answer = answer + 'Direct link: <a href="' + redirect_link + '">'
            answer = answer + link + '</a></p>'
            answer = answer + '<p class="links"> Access without Tor Browser: '
            answer = answer + '<a href="'
            answer = answer + redirect_tor2web_link + '">' + tor2web_link
            answer = answer + '</a></p>'
            answer = answer + description
            answer = answer + '<p class="urlinfo">' + pub_date + '</p></div>'
            answer = '<li class="hs_site">' + answer + '</li>'
            html_answer = html_answer + answer
        if not html_answer:
            html_answer = '<li class="hs_site"><h3>No search results</h3></li>'
        return html_answer
    except Exception as error:
        print error
        return '<li class="hs_site"><h3>No search results</h3></li>'
