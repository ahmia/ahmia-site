from django.template import Context, loader, RequestContext
from django.shortcuts import redirect, render_to_response
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib import auth
from datetime import datetime, timedelta
from ahmia.models import *
import hashlib
import simplejson
import urllib3

def query(request):
    if request.method == 'POST':
        data = request.raw_post_data
        xml = get_query(data)
        return HttpResponse(xml, content_type="application/xml")
    else:
        return HttpResponseBadRequest("Bad request")

def yacy_connection(request, query):
    if request.method == 'GET':
        query = query.replace(" ", "%20")
        http = urllib3.PoolManager()
        response = http.request('GET', "http://10.8.0.10:8090/"+query)
        #response = http.request('GET', "http://localhost:8090/"+query)
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
        return HttpResponseBadRequest("Bad request")

def find(request, query):
    if request.method == 'GET':
        if not query and 's' in request.GET:
            query = request.GET.get('s')
        xml = str(get_query(query))
        xml = xml.replace("/yacysearch.xsl", "/static/xslt/yacysearch.xsl")
        xml = xml.replace("<rss", "<lol")
        xml = xml.replace("</rss>", "</lol>")
        return HttpResponse(xml, content_type="application/xml")
    else:
        return HttpResponseBadRequest("Bad request")

#http://10.8.0.6:8090/yacysearch.rss?query=<search_string>&size=<max_hits>
def get_query(query):
    try:
        query = query.replace(" ", "%20")
        url = "http://10.8.0.10:8090/yacysearch.rss?query=" + query
        #url = "http://localhost:8090/yacysearch.rss?query=" + query
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        data = response.data
        return data
    except e as Exception:
        print e

def default(request):
    return redirect('ahmia.views.search_page')

def add(request):
    if request.method == 'GET':
        t = loader.get_template("add.html")
        c = Context({'count_banned': HiddenWebsite.objects.filter(banned=True).count(),
            'count_online': HiddenWebsite.objects.filter(banned=False, online=True).count()})
        return HttpResponse(t.render(c))
    else:
        return HttpResponseBadRequest("Bad request")

def banned(request):
    return banned_txt(request)

def onion_list(request):
    content_type = request.META.get('CONTENT_TYPE')
    if request.method == 'GET':
        if content_type and "json" in content_type:
            return onions_json(request)
        elif content_type and "rdf" in content_type:
            return onions_rdf(request)
        else: #default return is human readable HTML page
            return render_page('hs_list_view.html')
    elif request.method == 'POST':
        return post_add_hs(request)
    else:
        return HttpResponseBadRequest('Only GET or POST requests accepted.')

def onion_error(request, input):
    return HttpResponseBadRequest('Invalid onion domain.')

def onion(request, onion):
    hs_list = HiddenWebsiteDescription.objects.filter(about=onion)
    if hs_list:
        hs = hs_list.latest('updated')
    else:
        return HttpResponseBadRequest("There is no "+onion+" indexed. Please add it if it exists.")
    if request.method == 'GET':
        content_type = request.META.get('CONTENT_TYPE')
        if content_type and "json" in content_type:
            return onion_json(request, onion)
        elif content_type and "rdf" in content_type:
            return onion_rdf(request, onion)
        else: #default return is human readable HTML page
            if hs.about.banned:
                return HttpResponseBadRequest("This page is banned and it cannot be viewed.")
            t = loader.get_template("hs_view.html")
            c = Context({'description': hs,
                        'onion': onion,
                        'count_banned': HiddenWebsite.objects.filter(banned=True).count(),
                        'count_online': HiddenWebsite.objects.filter(banned=False, online=True).count()})
            return HttpResponse(t.render(c))
    elif request.method == 'PUT' and request.user.is_authenticated():
        return ban(request, onion)
    else:
        return HttpResponseBadRequest("Bad request")

def onion_edit(request, onion):
    if request.method == 'GET':
        hs_list = HiddenWebsiteDescription.objects.filter(about=onion)
        if hs_list:
            hs = hs_list.latest('updated')
        else:
            return HttpResponseBadRequest("There is no "+onion+" indexed. Please add it if it exists.")
        if hs.officialInfo:
            return HttpResponseBadRequest("This page has official info and it cannot be edited.")
        if hs.about.banned:
            return HttpResponseBadRequest("This page is banned and it cannot be edited.")
        t = loader.get_template('hs_edit.html')
        c = Context({'site': hs,
                    'count_banned': HiddenWebsite.objects.filter(banned=True).count(),
                    'count_online': HiddenWebsite.objects.filter(banned=False, online=True).count()})
        return HttpResponse(t.render(c))
    else:
        return HttpResponseBadRequest("Bad request")

def post_add_hs(request):
    postData = request.raw_post_data
    #build post to json form
    if postData.startswith('url'):
        url = request.POST.get('url', '')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        relation = request.POST.get('relation', '')
        subject = request.POST.get('subject', '')
        type = request.POST.get('type', '')
        sign = request.POST.get('sign', '')
        if sign != 'antispammer':
            return HttpResponse("Must have the anti-spam field filled.")
        raw_json = '{"url":"'+url+'","title":"'+title+'","description":"'+description+'","relation":"'+relation+'","subject":"'+subject+'","type":"'+type+'"}'
        json = simplejson.loads(raw_json)
    #json
    else:
        try:
            json = simplejson.loads(postData)
        except:
            return HttpResponse('Error: Invalid JSON data.')
    return add_hs(json, request)

def add_hs(json, request):
    url = json.get('url')
    relation = json.get('relation')
    id = url[7:-7]
    md5 = hashlib.md5(url[7:-1]).hexdigest()
    #official information cannot be edited
    hs_list = HiddenWebsiteDescription.objects.filter(about=id)
    hs = ""
    if hs_list:
        hs = hs_list.latest('updated')
    if hs and hs.officialInfo:
        return HttpResponseBadRequest("This page has official info and it cannot be edited.")
    if hs and hs.about.banned:
        return HttpResponseBadRequest("This page is banned and it cannot be edited.")
    if relation:
        regex = re.compile(
                    r'^(?:http|ftp)s?://' # http:// or https://
                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                    r'localhost|' #localhost...
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                    r'(?::\d+)?' # optional port
                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not regex.match(relation):
            json['relation'] = ""
    try:
        validate_onion_URL(url)
    except ValidationError:
        print "Invalid onion domain"
        return HttpResponseBadRequest("Error: Invalid URL! URL must be exactly like http://something.onion/")
    try:
        hs, created = HiddenWebsite.objects.get_or_create(id=id, url=url, md5=md5)
        if created:
            hs.online = False
            hs.banned = False
            hs.full_clean()
            hs.save()
        add_description(json, hs)
    except ValidationError as e:
        print "Invalid data."
        return HttpResponseBadRequest("Invalid data.")
    return HttpResponseRedirect("/address/"+id)

def add_description(json, hs):
    title = json.get('title')
    description = json.get('description')
    relation = json.get('relation')
    subject = json.get('subject')
    type = json.get('type')
    try:
        old_descr = HiddenWebsiteDescription.objects.filter(about=hs).latest('updated')
        descr = HiddenWebsiteDescription.objects.create(about=hs)
        if title:
            descr.title = title
        else:
            descr.title = old_descr.title
        if description:
            descr.description = description
        else:
            descr.description = old_descr.description
        #sometimes might be useful to actually destroy the relation
        if title:
            descr.relation = relation
        else:
            descr.relation = old_descr.relation
        if subject:
            descr.subject = subject
        else:
            descr.subject = old_descr.subject
        #sometimes might be useful to actually destroy the subject
        if title:
            descr.type = type
        else:
            descr.type = old_descr.type
        descr.officialInfo = False
        descr.full_clean()
        descr.save()
    except ValidationError as e:
        return
    except:
        descr = HiddenWebsiteDescription.objects.create(about=hs)
        descr.title = title
        descr.description = description
        descr.relation = relation
        descr.subject = subject
        descr.type = type
        descr.officialInfo = False
        descr.full_clean()
        descr.save()

def onion_json(request, onion):
    hs = HiddenWebsiteDescription.objects.filter(about=onion).latest('updated')
    t = loader.get_template('onion.json')
    c = Context({'hs': hs})
    return HttpResponse(t.render(c), content_type="application/json")

def onion_rdf(request, onion):
    hs = HiddenWebsiteDescription.objects.filter(about=onion).latest('updated')
    t = loader.get_template('onion.rdf')
    c = Context({'hs': hs})
    return HttpResponse(t.render(c), content_type="application/rdf+xml")

def onions_json(request):
    hs_list = HiddenWebsiteDescription.objects.order_by('about', '-updated').distinct('about')
    t = loader.get_template('onions.json')
    c = Context({'hs_list': hs_list})
    return HttpResponse(t.render(c), content_type="application/json")

def onions_rdf(request):
    hs_list = HiddenWebsiteDescription.objects.order_by('about', '-updated').distinct('about')
    t = loader.get_template('onions.rdf')
    c = Context({'hs_list': hs_list})
    return HttpResponse(t.render(c), content_type="application/rdf+xml")

def onions_txt(request):
    sites = HiddenWebsite.objects.filter(banned=False).order_by('url')
    list = []
    for site in sites:
        list.append(site.url+"\n")
    return HttpResponse(list, content_type="text/plain")

def all_onions_txt(request):
    sites = HiddenWebsite.objects.all().order_by('url')
    list = []
    for site in sites:
        list.append(site.url+"\n")
    return HttpResponse(list, content_type="text/plain")

def banned_txt(request):
    sites = HiddenWebsite.objects.filter(banned=True)
    md5_list = []
    for site in sites:
        md5_list.append(site.md5+"\n")
    return HttpResponse(md5_list, content_type="text/plain")

def banned_domains_plain(request):
    sites = HiddenWebsite.objects.filter(banned=True)
    url_list = []
    for site in sites:
        url_list.append(site.url+"\n")
    return HttpResponse(url_list, content_type="text/plain")

#return a page without any parameters
def render_page(page):
    onions = HiddenWebsite.objects.all()
    t = loader.get_template(page)
    c = Context({'description_list': HiddenWebsiteDescription.objects.order_by('about','-updated').distinct('about'),
        'count_banned': onions.filter(banned=True).count(),
        'count_online': onions.filter(banned=False,online=True).count()})
    return HttpResponse(t.render(c))

#policy
def policy(request):
    return render_page('policy.html')

#disclaimer
def disclaimer(request):
    return render_page('disclaimer.html')

#description proposal
def descriptionProposal(request):
    return render_page('descriptionProposal.html')

#create Hs description
def createHsDescription(request):
    return render_page('createHsDescription.html')

#documentation
def documentation(request):
    return render_page('documentation.html')

#about us
def about(request):
    return render_page('about.html')

#Google Summer of Code 2014 proposal
def gsoc(request):
    return render_page('gsoc.html')

#full text search
def search_page(request):
    return render_page('full_text_search.html')

#show IP address
def show_ip(request):
    ip = get_client_ip(request)
    return HttpResponse(ip)

#return ip address
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

#Administration login
def login(request):
    if request.method == 'GET':
        return render_to_response('login.html')
    elif request.method == 'POST':
        try:
            user = auth.authenticate(username=request.POST['username'],
                            password=request.POST['password'])
            if user is None:
                return render_to_response('login.html',
                    {'error': 'Invalid password', 'username':request.POST['username']})
            else:
                auth.login(request, user)
                return redirect('ahmia.views.rule')
        except KeyError:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()

#Administration logout
def logout(request):
    auth.logout(request)
    return redirect('ahmia.views.rule')

#Administration rule content
def rule(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            return render_page('rule.html')
        else:
            return redirect('ahmia.views.login')
    else:
        return HttpResponseBadRequest()

#test if service is online
#test descriptions
#socket to use Tor SOCKS4 proxy
import urllib2
import httplib
import socks

class SocksiPyConnection(httplib.HTTPConnection):
    def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=True, username=None, password=None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs)
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

class SocksiPyHandler(urllib2.HTTPHandler):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kw = kwargs
        urllib2.HTTPHandler.__init__(self)
    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=0):
            conn = SocksiPyConnection(*self.args, host=host, port=port, strict=strict, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)

#test if onion domain is up add get description if there is one
def onion_up(request, onion):
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except:
        return HttpResponseBadRequest("There is no "+onion+" indexed. Please add it if it exists.")
    if request.method == 'POST': # and request.user.is_authenticated():
        return hs_online_check(hs, onion)
    elif request.method == 'GET':
        #is this http server been online within 7 days
        if hs.online:
            return HttpResponse("up")
        else:
            return HttpResponse("down")
    else:
        return HttpResponseBadRequest("Bad request")

def hs_online_check(hs,onion):
    try:
        opener = urllib2.build_opener(SocksiPyHandler(socks.PROXY_TYPE_SOCKS4, '127.0.0.1', 9050))
        handle = opener.open('http://'+str(onion)+'.onion/')
        code = handle.getcode()
        print code
        #it is up!
        if code != 404:
            hs.seenOnline = datetime.now()
            hs.online = True
            hs.save()
            try:
                handle = opener.open('http://'+str(onion)+'.onion/description.json')
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
            except Exception as e:
                print e
            return HttpResponse("up")
        else:
            if not hs.seenOnline or (datetime.now() - hs.seenOnline) > timedelta(days=7):
                hs.online = False
                hs.save()
            return HttpResponse("down")
    except Exception as e:
        print e
        return HttpResponse("down")

def add_official_info(json, hs):
    title = json.get('title')
    description = json.get('description')
    relation = json.get('relation')
    subject = json.get('keywords')
    type = json.get('type')
    lan = json.get('language')
    contact = json.get('contactInformation')
    descr = HiddenWebsiteDescription.objects.create(about=hs)
    descr.title = take_first_from_list(title)
    descr.description = take_first_from_list(description)
    descr.relation = take_first_from_list(relation)
    descr.subject = take_first_from_list(subject)
    descr.type = take_first_from_list(type)
    descr.contactInformation = take_first_from_list(contact)
    descr.language = take_first_from_list(lan)
    descr.officialInfo = True
    descr.full_clean()
    descr.save()

def take_first_from_list(list):
    if not list:
        return ""
    elif isinstance(list, basestring):
        return list
    else:
        return list[0]

def ban(request,onion):
    hs_list = HiddenWebsite.objects.filter(id=onion)
    if hs_list:
        hs = hs_list.latest('updated')
    else:
        answer = "There is no "+onion+" indexed. Please add it if it exists."
        return HttpResponseBadRequest(answer)
    hs.banned = True
    hs.full_clean()
    hs.save()
    return HttpResponse("banned")
