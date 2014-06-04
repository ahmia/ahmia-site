"""Basic views."""
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from ahmia.models import HiddenWebsite, HiddenWebsitePopularity
from ahmia.models import HiddenWebsiteDescription
import hashlib
import simplejson
import re # Regular expressions
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import ahmia.view_help_functions as helpers # My view_help_functions.py
import ahmia.views_admin # My views_admin.py
from django.conf import settings # For the SMTP settings

def add(request):
    """Add form for a new .onion address."""
    if request.method == 'GET':
        template = loader.get_template("add.html")
        onions = HiddenWebsite.objects.all()
        count_online = onions.filter(banned=False, online=True).count()
        count_banned = onions.filter(banned=True).count()
        content = Context({'count_banned': count_banned,
            'count_online': count_online})
        return HttpResponse(template.render(content))
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def banned(request):
    """Return the plain text MD5 sums of the banned onions."""
    return banned_txt(request)

def onion_list(request):
    """List the onion addresses."""
    content_type = request.META.get('CONTENT_TYPE')
    if request.method == 'GET':
        if content_type and "json" in content_type:
            return onions_json(request)
        elif content_type and "rdf" in content_type:
            return onions_rdf(request)
        else: #default return is human readable HTML page
            return helpers.render_page('hs_list_view.html')
    elif request.method == 'POST':
        return post_add_hs(request)
    else:
        return HttpResponseNotAllowed("Only GET and POST request are allowed.")

def onion_error(request, input_str):
    """If the /address/something is not valid something.onion."""
    method = request.method
    if method in ['GET', 'HEAD', 'POST', 'DELETE', 'PUT']:
        return HttpResponseBadRequest('Invalid onion domain: ' + input_str)

def single_onion(request, onion):
    """Edits, bans or shows an onion site."""
    hs_list = HiddenWebsiteDescription.objects.filter(about=onion)
    if hs_list:
        hs = hs_list.latest('updated')
    else:
        answer = "There is no %s.onion indexed." % onion
        return HttpResponseNotFound(answer)
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
            template = loader.get_template("hs_view.html")
            onions = HiddenWebsite.objects.all()
            count_banned = onions.filter(banned=True).count()
            count_online = onions.filter(banned=False, online=True).count()
            content = Context({'description': hs,
            'onion': onion,
            'count_banned': count_banned,
            'count_online': count_online})
            return HttpResponse(template.render(content))
    elif request.method == 'PUT':
        return put_data_to_onion(request, onion)
    elif request.method == 'DELETE':
        # Delete means ban
        return views_admin.ban(request, onion)
    else:
        answer = "Only GET, PUT and DELETE request are allowed."
        return HttpResponseNotAllowed(answer)

def put_data_to_onion(request, onion):
    """Add data to hidden service."""
    try:
        json_obj = simplejson.loads(request.body)
        abuse_note = json_obj.get("abuse_note")
        url = json_obj.get("url")
        message = "User sended abuse notice: \n\n URL: " + url
        message = message + "\n\n User message: " + abuse_note
        send_mail('Abuse notice', message, settings.DEFAULT_FROM_EMAIL,
        settings.RECIPIENT_LIST, fail_silently=False)
        return HttpResponse('Abuse notice sended.')
    except Exception as error:
        print "Error: %s" % onion
        print "Error: %s" % error
        return HttpResponseBadRequest(error)

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
        except ObjectDoesNotExist:
            print "Redirecting unknown: http://" + onion + ".onion/"
            message = "Redirecting to hidden service."
            return helpers.redirect_page(message, 0, redirect_url)
        try:
            pop, creat = HiddenWebsitePopularity.objects.get_or_create(about=hs)
            if creat or hs.banned:
                pop.clicks = 0
                pop.public_backlinks = 0
                pop.tor2web = 0
            pop.clicks = pop.clicks + 1
            pop.full_clean()
            pop.save()
        except Exception as error:
            print error
            return HttpResponseBadRequest("Bad request")
        message = "Redirecting to hidden service."
        return helpers.redirect_page(message, 0, redirect_url)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def onion_popularity(request, onion):
    """Return the popularity statistics of an onion."""
    if request.method == 'GET':
        try:
            hs = HiddenWebsite.objects.get(id=onion)
        except ObjectDoesNotExist:
            answer = "There is no %s.onion indexed." % onion
            return HttpResponseNotFound(answer)
        try:
            popularity = HiddenWebsitePopularity.objects.get(about=hs)
        except ObjectDoesNotExist:
            answer = "No popularity data about %s.onion." % onion
            return HttpResponseNotFound("No popularity data about %s.onion.")
        if hs.banned:
            return HttpResponseNotAllowed("This page is banned.")
        template = loader.get_template('onion_popularity.json')
        content = Context({'popularity': popularity})
        type_str = "application/json"
        return HttpResponse(template.render(content), content_type=type_str)
    elif request.method == 'PUT':
        # Allow POST data only from the localhost
        ip_addr = helpers.get_client_ip(request)
        if not str(ip_addr) in "127.0.0.1":
            answer = "Bad request: only allowed form the localhost."
            return HttpResponseBadRequest(answer)
        else:
            # Add new data
            data = request.raw_post_data
            return add_popularity(data, onion)
    else:
        return HttpResponseNotAllowed("Only GET and PUT requests are allowed.")

def add_popularity(data, onion):
    """Add new popularity information to hidden service."""
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except ObjectDoesNotExist:
        answer = "There is no %s.onion indexed." % onion
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
    except Exception as error:
        print error
        return HttpResponseBadRequest("Unknown error.")

def onion_edit(request, onion):
    """The edit form for an onion site."""
    if request.method == 'GET':
        hs_list = HiddenWebsiteDescription.objects.filter(about=onion)
        if hs_list:
            hs = hs_list.latest('updated')
        else:
            answer = "There is no %s.onion indexed." % onion
            return HttpResponseNotFound(answer)
        if hs.officialInfo:
            answer = "This page has official info and it cannot be edited."
            return HttpResponseNotAllowed(answer)
        if hs.about.banned:
            answer = "This page is banned and it cannot be edited."
            return HttpResponseNotAllowed(answer)
        template = loader.get_template('hs_edit.html')
        onions = HiddenWebsite.objects.all()
        count_banned = onions.filter(banned=True).count()
        count_online = onions.filter(banned=False, online=True).count()
        content = Context({'site': hs,
                    'count_banned': count_banned,
                    'count_online': count_online})
        return HttpResponse(template.render(content))
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def post_add_hs(request):
    """The post JSON data about .onion address."""
    post_data = request.raw_post_data
    #build post to json form
    if post_data.startswith('url'):
        url = request.POST.get('url', '')
        # Add the / in the end if it lacks
        # http://something.onion => http://something.onion/
        url = url.strip(' \t\n\r')
        if url and url[-1] != "/":
            url = url + "/"
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        relation = request.POST.get('relation', '')
        subject = request.POST.get('subject', '')
        type_str = request.POST.get('type', '')
        sign = request.POST.get('sign', '')
        if sign != 'antispammer':
            return HttpResponse("Must have the anti-spam field filled.")
        raw_json = '{"url":"'+url+'","title":"'+title+'","description":"'
        raw_json = raw_json+description+'","relation":"'+relation
        raw_json = raw_json+'","subject":"'+subject+'","type":"'+type_str+'"}'
        json = simplejson.loads(raw_json)
    #json
    else:
        try:
            json = simplejson.loads(post_data)
        except:
            return HttpResponse('Error: Invalid JSON data.')
    return add_hs(json)

def add_hs(json):
    """Adds an onion address description JSON data to the onion."""
    url = json.get('url')
    relation = json.get('relation')
    id_str = url[7:-7]
    md5 = hashlib.md5(url[7:-1]).hexdigest()
    #official information cannot be edited
    hs_list = HiddenWebsiteDescription.objects.filter(about=id_str)
    if hs_list:
        hs = hs_list.latest('updated')
        if hs.officialInfo:
            answer = "This page has official info and it cannot be edited."
            return HttpResponseBadRequest(answer)
        if hs.about.banned:
            answer = "This page is banned and it cannot be edited."
            return HttpResponseBadRequest(answer)
    if relation:
        regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        # Domain
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not regex.match(relation):
            json['relation'] = ""
    try:
        helpers.validate_onion_url(url)
    except ValidationError:
        print "Invalid onion domain"
        answer = "Invalid URL! URL must be exactly like http://something.onion/"
        return HttpResponseBadRequest(answer)
    try:
        hs, creat = HiddenWebsite.objects.get_or_create(id=id_str, url=url, md5=md5)
        if creat:
            hs.online = False
            hs.banned = False
            hs.full_clean()
            hs.save()
        add_description(json, hs)
    except ValidationError as error:
        print "Invalid data: %s" % error
        return HttpResponseBadRequest("Invalid data.")
    message = 'Hidden service added.'
    redirect_url = '/address/'+id_str
    return helpers.redirect_page(message, 3, redirect_url)

def add_description(json, hs):
    """Add description JSON data."""
    title = json.get('title')
    description = json.get('description')
    relation = json.get('relation')
    subject = json.get('subject')
    type_str = json.get('type')
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
            descr.type = type_str
        else:
            descr.type = old_descr.type
        descr.officialInfo = False
        descr.full_clean()
        descr.save()
    except ValidationError as error:
        print error
        return
    except:
        descr = HiddenWebsiteDescription.objects.create(about=hs)
        descr.title = title
        descr.description = description
        descr.relation = relation
        descr.subject = subject
        descr.type = type_str
        descr.officialInfo = False
        descr.full_clean()
        descr.save()

def onion_json(request, onion):
    """Onion information as a JSON file."""
    if request.method == 'GET':
        hss = HiddenWebsiteDescription.objects.filter(about=onion)
        hs = hss.latest('updated')
        template = loader.get_template('onion.json')
        content = Context({'hs': hs})
        type_str = "application/json"
        return HttpResponse(template.render(content), content_type=type_str)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def onion_rdf(request, onion):
    """Onion information as an RDF file."""
    if request.method == 'GET':
        hss = HiddenWebsiteDescription.objects.filter(about=onion)
        hs = hss.latest('updated')
        template = loader.get_template('onion.rdf')
        content = Context({'hs': hs})
        type_str = "application/rdf+xml"
        return HttpResponse(template.render(content), content_type=type_str)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def onions_json(request):
    """All onion information as a JSON file."""
    if request.method == 'GET':
        hs_list = HiddenWebsiteDescription.objects.order_by('about', '-updated')
        hs_list = hs_list.distinct('about')
        template = loader.get_template('onions.json')
        content = Context({'hs_list': hs_list})
        type_str = "application/json"
        return HttpResponse(template.render(content), content_type=type_str)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def onions_rdf(request):
    """All onion information as a RDF file."""
    if request.method == 'GET':
        hs_list = HiddenWebsiteDescription.objects.order_by('about', '-updated')
        hs_list = hs_list.distinct('about')
        template = loader.get_template('onions.rdf')
        content = Context({'hs_list': hs_list})
        type_str = "application/rdf+xml"
        return HttpResponse(template.render(content), content_type=type_str)
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def onions_txt(request):
    """Plain text list of an onion pages."""
    if request.method == 'GET':
        sites = HiddenWebsite.objects.filter(banned=False).order_by('url')
        site_list = []
        for site in sites:
            site_list.append(site.url+"\n")
        return HttpResponse(site_list, content_type="text/plain")
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def onions_online_txt(request):
    """Return all domains that are online and are not banned."""
    if request.method == 'GET':
        sites = HiddenWebsite.objects.filter(online=True, banned=False)
        sites = sites.order_by('url')
        site_list = []
        for site in sites:
            site_list.append(site.url+"\n")
        return HttpResponse(site_list, content_type="text/plain")
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def all_onions_txt(request):
    """Return a plain text list of onions including the banned ones."""
    # Allow requests only from the localhost
    ip_addr = helpers.get_client_ip(request)
    if not str(ip_addr) in "127.0.0.1":
        answer = "Bad request: only allowed form the localhost."
        return HttpResponseBadRequest(answer)
    sites = HiddenWebsite.objects.all().order_by('url')
    site_list = []
    for site in sites:
        site_list.append(site.url+"\n")
    return HttpResponse(site_list, content_type="text/plain")

def banned_txt(request):
    """Return the plain text MD5 sums of the banned onions."""
    if request.method == 'GET':
        sites = HiddenWebsite.objects.filter(banned=True)
        md5_list = []
        for site in sites:
            md5_list.append(site.md5+"\n")
        return HttpResponse(md5_list, content_type="text/plain")
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def banned_domains_plain(request):
    """Return the plain text list of banned onions."""
    # Allow requests only from the localhost
    ip_addr = helpers.get_client_ip(request)
    if not str(ip_addr) in "127.0.0.1":
        answer = "Bad request: only allowed form the localhost."
        return HttpResponseBadRequest(answer)
    sites = HiddenWebsite.objects.filter(banned=True)
    url_list = []
    for site in sites:
        url_list.append(site.url+"\n")
    return HttpResponse(url_list, content_type="text/plain")
