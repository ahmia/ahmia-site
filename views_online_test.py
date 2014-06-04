"""

Views
Test if service is online.
Or just show the online status.
Use local socks proxy that is the Tor connection.

"""
from django.http import HttpResponse, HttpResponseNotFound
from django.http import HttpResponseNotAllowed
from datetime import datetime, timedelta
from ahmia.models import HiddenWebsite, HiddenWebsiteDescription
from django.core.exceptions import ObjectDoesNotExist
import simplejson
from bs4 import BeautifulSoup #To parse HTML

#For socks connection
import urllib2
import httplib
import socks

class SocksiPyConnection(httplib.HTTPConnection):
    """Socks connection for HTTP."""
    def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=True,
    username=None, password=None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns,
        username, password)
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs)
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

class SocksiPyHandler(urllib2.HTTPHandler):
    """Socks connection for HTTP."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kw = kwargs
        urllib2.HTTPHandler.__init__(self)
    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=0):
            """Build connection."""
            conn = SocksiPyConnection(*self.args, host=host, port=port,
            strict=strict, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)

def onion_up(request, onion):
    """Test if onion domain is up add get description if there is one."""
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except ObjectDoesNotExist:
        answer = "There is no "+onion+" indexed. Please add it if it exists."
        return HttpResponseNotFound(answer)
    if request.method == 'POST': # and request.user.is_authenticated():
        remove_historical_descriptions(hs)
        return hs_online_check(onion)
    elif request.method == 'GET':
        #is this http server been online within 7 days
        if hs.online:
            return HttpResponse("up")
        else:
            return HttpResponse("down")
    else:
        return HttpResponseNotAllowed("Only GET and POST is allowed.")

def hs_online_check(onion):
    """Online check for hidden service."""
    try:
        return hs_http_checker(onion)
    except Exception as error:
        print error
        return HttpResponse("down")

def hs_http_checker(onion):
    """Socks connection to the Tor network. Try to download an onion."""
    socks_con = SocksiPyHandler(socks.PROXY_TYPE_SOCKS4, '127.0.0.1', 9050)
    opener = urllib2.build_opener(socks_con)
    return hs_downloader(opener, onion)

def hs_downloader(opener, onion):
    """Try to download the front page and description.json."""
    handle = opener.open('http://'+str(onion)+'.onion/')
    code = handle.getcode()
    print "Site answers to the online check with code %d." % code
    if code != 404: # It is up
        analyze_front_page(handle.read(), onion)
        hs_download_description(opener, onion)
        hs = HiddenWebsite.objects.get(id=onion)
        hs.seenOnline = datetime.now()
        hs.online = True
        hs.save()
        return HttpResponse("up")
    else:
        hs = HiddenWebsite.objects.get(id=onion)
        if not hs.seenOnline:
            hs.online = False
            hs.save()
        else:
            # Test if hidden service has been online during this week
            # If it hasn't been online a week,
            # then it is officially offline
            last_seen_online = datetime.now() - hs.seenOnline
            if last_seen_online > timedelta(days=7):
                hs.online = False
                hs.save()
        return HttpResponse("down")

def analyze_front_page(raw_html, onion):
    """Analyze raw HTML page."""
    try:
        soup = BeautifulSoup(raw_html)
        title_element = soup.find('title')
        desc_element = soup.find(attrs={"name":"description"})
        keywords_element = soup.find(attrs={"name":"keywords"})
        title = ""
        keywords = ""
        description = ""
        h1_element = soup.find('h1')
        if title_element:
            title = title_element.string.encode('utf-8')
        if desc_element and desc_element['content']:
            description = desc_element['content'].encode('utf-8')
        if keywords_element and keywords_element['content']:
            keywords = keywords_element['content'].encode('utf-8')
        if not title and h1_element:
            title = h1_element.string.encode('utf-8')
        if title or keywords or description:
            fill_description(onion, title, keywords, description)
    except Exception as error:
        print error

def fill_description(onion, title, keywords, description):
    """Fill description information if there are none."""
    hs = HiddenWebsite.objects.get(id=onion)
    old_descriptions = HiddenWebsiteDescription.objects.filter(about=hs)
    relation = ""
    site_type = ""
    if old_descriptions:
        old_descr = old_descriptions.latest('updated')
        # Do nothing with the official info
        if old_descr.officialInfo:
            return
        # Do nothing if the title, description and subject already exists
        if old_descr.title and old_descr.description and old_descr.subject:
            return
        # Else use the old content as much as possible
        if old_descr.title:
            title = old_descr.title
        if old_descr.description:
            description = old_descr.description
        if old_descr.subject:
            keywords = old_descr.subject
        if old_descr.relation:
            relation = old_descr.relation
        if old_descr.type:
            site_type = old_descr.type
    descr = HiddenWebsiteDescription.objects.create(about=hs)
    descr.title = title
    descr.description = description
    descr.relation = relation
    descr.subject = keywords
    descr.type = site_type
    descr.officialInfo = False
    descr.full_clean()
    descr.save()

def hs_download_description(opener, onion):
    """Try to download description.json."""
    try:
        dec_url = 'http://'+str(onion)+'.onion/description.json'
        handle = opener.open(dec_url)
        descr = handle.read()
        try:
            # There cannot be that big descriptions
            if len(descr) < 5000:
                descr = descr.replace('\r', '')
                descr = descr.replace('\n', '')
                json = simplejson.loads(descr)
                add_official_info(json, onion)
        except:
            print "Adding this JSON failed:"
            print descr
    except Exception as error:
        print error

def remove_historical_descriptions(hs):
    """Remove old descriptions."""
    descriptions = HiddenWebsiteDescription.objects.filter(about=hs)
    descriptions = descriptions.order_by('-updated')
    if len(descriptions) > 3:
        for desc in descriptions[3:]:
            desc.delete()

def add_official_info(json, onion):
    """Add official description.json information to the ahmia."""
    title = json.get('title')
    description = json.get('description')
    relation = json.get('relation')
    subject = json.get('keywords')
    hs_type = json.get('type')
    lan = json.get('language')
    contact = json.get('contactInformation')
    hs = HiddenWebsite.objects.get(id=onion)
    descr = HiddenWebsiteDescription.objects.create(about=hs)
    descr.title = take_first_from_list(title)
    descr.description = take_first_from_list(description)
    descr.relation = take_first_from_list(relation)
    descr.subject = take_first_from_list(subject)
    descr.type = take_first_from_list(hs_type)
    descr.contactInformation = take_first_from_list(contact)
    descr.language = take_first_from_list(lan)
    descr.officialInfo = True
    descr.full_clean()
    descr.save()

def take_first_from_list(test_list):
    """Return the first from the list."""
    if not test_list:
        return ""
    elif isinstance(test_list, basestring):
        return test_list
    else:
        return test_list[0]
