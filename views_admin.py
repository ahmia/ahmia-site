"""

Views
Site admin features.
Helps to rule the content and ban sites etc.

"""
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect, render_to_response
from django.contrib import auth
from ahmia import view_help_functions # My view_help_functions.py
from ahmia.models import HiddenWebsite, HiddenWebsitePopularity
from django.core.exceptions import ObjectDoesNotExist

def login(request):
    """Administration login."""
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
                return redirect('ahmia.views_admin.rule')
        except KeyError:
            return HttpResponseBadRequest()
    else:
        return HttpResponseNotAllowed("Only GET or POST requests are allowed.")

def logout(request):
    """Administration logout."""
    auth.logout(request)
    return redirect('ahmia.views_admin.rule')

def rule(request):
    """Administration rule content"""
    if request.method == 'GET':
        if request.user.is_authenticated():
            return view_help_functions.render_page('rule.html')
        else:
            return redirect('ahmia.views_admin.login')
    else:
        return HttpResponseNotAllowed("Only GET request is allowed.")

def ban(request, onion):
    """Bans an onion site."""
    if not request.user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)
    hs_list = HiddenWebsite.objects.filter(id=onion)
    if hs_list:
        hs = hs_list.latest('updated')
    else:
        answer = "There is no "+onion+" indexed. Please add it if it exists."
        return HttpResponseNotFound(answer)
    hs.banned = True
    hs.full_clean()
    hs.save()
    try:
        popularity = HiddenWebsitePopularity.objects.get(about=hs)
        popularity.clicks = 0
        popularity.public_backlinks = 0
        popularity.tor2web = 0
        popularity.save()
    except ObjectDoesNotExist:
        print "No popularity for this banned onion."
    return HttpResponse("banned")
