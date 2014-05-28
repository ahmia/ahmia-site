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
        return hs_online_check(hs, onion)
    elif request.method == 'GET':
        #is this http server been online within 7 days
        if hs.online:
            return HttpResponse("up")
        else:
            return HttpResponse("down")
    else:
        return HttpResponseNotAllowed("Only GET and POST is allowed.")

def hs_online_check(hs, onion):
    """Online check for hidden service."""
    try:
        socks_con = SocksiPyHandler(socks.PROXY_TYPE_SOCKS4, '127.0.0.1', 9050)
        opener = urllib2.build_opener(socks_con)
        handle = opener.open('http://'+str(onion)+'.onion/')
        code = handle.getcode()
        print code
        #it is up!
        if code != 404:
            hs.seenOnline = datetime.now()
            hs.online = True
            hs.save()
            try:
                dec_url = 'http://'+str(onion)+'.onion/description.json'
                handle = opener.open(dec_url)
                descr = handle.read()
                try:
                    #really, there cannot be that big descriptions
                    if len(descr) > 5000:
                        return HttpResponse("up")
                    descr = descr.replace('\r', '')
                    descr = descr.replace('\n', '')
                    json = simplejson.loads(descr)
                    add_official_info(json, hs)
                except:
                    print "Adding this JSON failed:"
                    print descr
            except Exception as error:
                print error
            return HttpResponse("up")
        else:
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
    except Exception as error:
        print error
        return HttpResponse("down")

def remove_historical_descriptions(hs):
    """Remove old descriptions."""
    descriptions = HiddenWebsiteDescription.objects.filter(about=hs)
    descriptions = descriptions.order_by('-updated')
    if len(descriptions) > 3:
        for desc in descriptions[3:]:
            desc.delete()

def add_official_info(json, hs):
    """Add official description.json information to the ahmia."""
    title = json.get('title')
    description = json.get('description')
    relation = json.get('relation')
    subject = json.get('keywords')
    hs_type = json.get('type')
    lan = json.get('language')
    contact = json.get('contactInformation')
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
