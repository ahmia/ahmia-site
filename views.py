from django.template import Context, loader, RequestContext
from django.shortcuts import redirect, render_to_response
from django.http import *
from django.contrib import auth
from datetime import datetime, timedelta
from ahmia.models import *
import hashlib
import simplejson
import urllib3
from django.core import serializers
from ahmia import view_help_functions # My view_help_functions.py

def add(request):
    if request.method == 'GET':
        t = loader.get_template("add.html")
        onions = HiddenWebsite.objects.all()
        count_online = onions.filter(banned=False, online=True).count()
        count_banned = onions.filter(banned=True).count()
        c = Context({'count_banned': count_banned,
            'count_online': count_online})
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
            return view_help_functions.render_page('hs_list_view.html')
    elif request.method == 'POST':
        return post_add_hs(request)
    else:
        return HttpResponseBadRequest('Only GET or POST requests accepted.')

def onion_error(request, input):
    return HttpResponseBadRequest('Invalid onion domain.')

def onion(request, onion):
    """Edits, bans or shows an onion site."""
    hs_list = HiddenWebsiteDescription.objects.filter(about=onion)
    if hs_list:
        hs = hs_list.latest('updated')
    else:
        answer = "There is no "+onion+" indexed. Please add it if it exists."
        return HttpResponseBadRequest(answer)
    if request.method == 'GET':
        content_type = request.META.get('CONTENT_TYPE')
        if content_type and "json" in content_type:
            return onion_json(request, onion)
        elif content_type and "rdf" in content_type:
            return onion_rdf(request, onion)
        else: #default return is human readable HTML page
            if hs.about.banned:
                answer = "This page is banned and it cannot be viewed."
                return HttpResponseBadRequest()
            t = loader.get_template("hs_view.html")
            onions = HiddenWebsite.objects.all()
            count_banned = onions.filter(banned=True).count()
            count_online = onions.filter(banned=False, online=True).count()
            c = Context({'description': hs,
                        'onion': onion,
                        'count_banned': count_banned,
                        'count_online': count_online})
            return HttpResponse(t.render(c))
    elif request.method == 'PUT':
        return put_data_to_onion(request, onion)
    elif request.method == 'DELETE' and request.user.is_authenticated():
        # Delete means ban
        return ban(request, onion)
    else:
        return HttpResponseBadRequest("Bad request")
    
def put_data_to_onion(request, onion):
    """Add data to hidden service."""
    return HttpResponseBadRequest("Bad request")

def onion_redirect(request):
    """Add clicked information and redirect to .onion address."""
    if request.method == 'GET':
        redirect_url = request.GET.get('redirect_url', '')
        if not redirect_url:
            answer = "Bad request: no GET parameter URL."
            return HttpResponseBadRequest(answer)
        onion = redirect_url.split("://")[1][:16]
        try:
            hs = HiddenWebsite.objects.get(id=onion)
        except:
            print "Redirecting unknown: http://" + onion + ".onion/"
            message = "Redirecting to hidden service."
            return redirect_page(message, 0, redirect_url)
        try:
            popularity, created = HiddenWebsitePopularity.objects.get_or_create(about=hs)
            if created or hs.banned:
                popularity.clicks = 0
                popularity.public_backlinks = 0
                popularity.tor2web = 0
            popularity.clicks = popularity.clicks + 1
            popularity.full_clean()
            popularity.save()
        except Exception as error:
            print error
            return HttpResponseBadRequest("Bad request")
        return redirect_page("Redirecting to hidden service.", 0, redirect_url)
    else:
        return HttpResponseBadRequest("Bad request")

def redirect_page(message, time, url):
    t = loader.get_template('redirect.html')
    c = Context({'message': message,
    'time': time,
    'redirect': url})
    return HttpResponse(t.render(c)) 

def onion_popularity(request, onion):
    if request.method == 'GET':
        try:
            hs = HiddenWebsite.objects.get(id=onion)
        except:
            answer = "There is no " + onion
            + ".onion indexed. Please add it if it exists."
            return HttpResponseNotFound(answer)
        try:
            popularity = HiddenWebsitePopularity.objects.get(about=hs)
        except:
            return HttpResponseBadRequest("There is no popularity data about "
            + onion + ".onion.")
        if hs.banned:
            return HttpResponseBadRequest("This page is banned.")
        t = loader.get_template('onion_popularity.json')
        c = Context({'popularity': popularity})
        return HttpResponse(t.render(c), content_type="application/json")
    elif request.method == 'PUT':
        # Allow POST data only from the localhost
        ip_addr = view_help_functions.get_client_ip(request)
        if not str(ip_addr) in "127.0.0.1":
            answer = "Bad request: only allowed form the localhost."
            return HttpResponseBadRequest(answer)
        else:
            # Add new data
            data = request.raw_post_data
            return add_popularity(data, onion)
    else:
        return HttpResponseBadRequest("Bad request")

def add_popularity(data, onion):
    """Add new popularity information to hidden service."""
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except:
        answer = "There is no " + onion
        + ".onion indexed. Please add it if it exists."
        return HttpResponseNotFound(answer)
    try:
        json_data = simplejson.loads(data)
    except:
        return HttpResponseBadRequest('Error: Invalid JSON data.')
    try:
        pop, created = HiddenWebsitePopularity.objects.get_or_create(about=hs)
        if created or hs.banned:
            pop.clicks = 0
            pop.public_backlinks = 0
            pop.tor2web = 0
        if hs.banned:
            return HttpResponse('No popularity tracking for banned sites.')
        if json_data.get('clicks'):
            pop.clicks = json_data.get('clicks')
        if json_data.get('backlinks'):
            pop.public_backlinks = json_data.get('backlinks')
        if json_data.get('tor2web_access_count'):
            # There are four Tor2web nodes
            # This mechanism reduces the number of Tor2web visits saved
            pop.tor2web = (pop.tor2web+json_data.get('tor2web_access_count'))/2
        pop.full_clean()
        pop.save()
        return HttpResponse('Popularity added.')
    except ValidationError as error:
        print "Invalid data: %s" % error
        return HttpResponseBadRequest("Invalid data.")
    except Exception as e:
        print e
        return HttpResponseBadRequest("Unknown error.")

def onion_edit(request, onion):
    if request.method == 'GET':
        hs_list = HiddenWebsiteDescription.objects.filter(about=onion)
        if hs_list:
            hs = hs_list.latest('updated')
        else:
            answer = "There is no " + onion
            + " indexed. Please add it if it exists."
            return HttpResponseBadRequest(answer)
        if hs.officialInfo:
            answer = "This page has official info and it cannot be edited."
            return HttpResponseBadRequest(answer)
        if hs.about.banned:
            answer = "This page is banned and it cannot be edited."
            return HttpResponseBadRequest(answer)
        t = loader.get_template('hs_edit.html')
        onions = HiddenWebsite.objects.all()
        count_banned = onions.filter(banned=True).count()
        count_online = onions.filter(banned=False, online=True).count()
        c = Context({'site': hs,
                    'count_banned': count_banned,
                    'count_online': count_online})
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
        raw_json = '{"url":"'+url+'","title":"'+title+'","description":"'
        +description+'","relation":"'+relation+'","subject":"'+subject
        +'","type":"'+type+'"}'
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
        answer = "This page has official info and it cannot be edited."
        return HttpResponseBadRequest(answer)
    if hs and hs.about.banned:
        answer = "This page is banned and it cannot be edited."
        return HttpResponseBadRequest(answer)
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
        validate_onion_url(url)
    except ValidationError:
        print "Invalid onion domain"
        answer = "Invalid URL! URL must be exactly like http://something.onion/"
        return HttpResponseBadRequest(answer)
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
    return redirect_page('Hidden service added.', 3, '/address/'+id)

def add_description(json, hs):
    title = json.get('title')
    description = json.get('description')
    relation = json.get('relation')
    subject = json.get('subject')
    type = json.get('type')
    try:
        descriptions = HiddenWebsiteDescription.objects.filter(about=hs)
        old_descr = descriptions.latest('updated')
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
    hs_list = HiddenWebsiteDescription.objects.order_by('about', '-updated')
    hs_list = hs_list.distinct('about')
    t = loader.get_template('onions.json')
    c = Context({'hs_list': hs_list})
    return HttpResponse(t.render(c), content_type="application/json")

def onions_rdf(request):
    hs_list = HiddenWebsiteDescription.objects.order_by('about', '-updated')
    hs_list = hs_list.distinct('about')
    t = loader.get_template('onions.rdf')
    c = Context({'hs_list': hs_list})
    return HttpResponse(t.render(c), content_type="application/rdf+xml")

def onions_txt(request):
    sites = HiddenWebsite.objects.filter(banned=False).order_by('url')
    list = []
    for site in sites:
        list.append(site.url+"\n")
    return HttpResponse(list, content_type="text/plain")

def onions_online_txt(request):
    """Return all domains that are online and are not banned."""
    sites = HiddenWebsite.objects.filter(online=True, banned=False)
    sites = sites.order_by('url')
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

#policy
def policy(request):
    return view_help_functions.render_page('policy.html')

#disclaimer
def disclaimer(request):
    return view_help_functions.render_page('disclaimer.html')

#description proposal
def descriptionProposal(request):
    return view_help_functions.render_page('descriptionProposal.html')

#create Hs description
def createHsDescription(request):
    return view_help_functions.render_page('createHsDescription.html')

#documentation
def documentation(request):
    return view_help_functions.render_page('documentation.html')

#about us
def about(request):
    return view_help_functions.render_page('about.html')

#Google Summer of Code 2014 proposal
def gsoc(request):
    return view_help_functions.render_page('gsoc.html')

#show IP address
def show_ip(request):
    ip_addr = view_help_functions.get_client_ip(request)
    return HttpResponse(ip_addr)

#Administration login
def login(request):
    if request.method == 'GET':
        return render_to_response('login.html')
    elif request.method == 'POST':
        try:
            user = auth.authenticate(username=request.POST['username'],
                            password=request.POST['password'])
            if user is None:
                username = request.POST['username']
                return render_to_response('login.html',
                    {'error': 'Invalid password', 'username': username})
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
            return view_help_functions.render_page('rule.html')
        else:
            return redirect('ahmia.views.login')
    else:
        return HttpResponseBadRequest()

def ban(request,onion):
    """Bans an onion site."""
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
