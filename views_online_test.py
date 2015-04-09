"""

Views
Test if service is online.
Or just show the online status.
Use local socks proxy that is the Tor connection.

"""
from datetime import datetime, timedelta

import simplejson
from django.core.exceptions import ObjectDoesNotExist
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseNotFound)
from django.views.decorators.http import require_http_methods

import ahmia.view_help_functions as helpers  # My view_help_functions.py
from ahmia.models import HiddenWebsite, HiddenWebsiteDescription


@require_http_methods(["GET", "PUT"])
def onion_up(request, onion):
    """Test if onion domain is up add get description if there is one."""
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except ObjectDoesNotExist:
        answer = "There is no "+onion+" indexed. Please add it if it exists."
        return HttpResponseNotFound(answer)
    if request.method == 'PUT': # and request.user.is_authenticated():
        ip_addr = helpers.get_client_ip(request)
        if not str(ip_addr) in "127.0.0.1":
            answer = "Only allowed form the localhost."
            return HttpResponseForbidden(answer)
        else:
            remove_historical_descriptions(onion)
            # If there is no request body, the onion is offline
            is_online = bool(request.body)
            # Log (store) online status
            hs.add_status(online=is_online)

            if is_online:
                try:
                    json_data = request.body
                    return add_info(json_data, onion)
                except Exception as error:
                    return HttpResponseBadRequest(error)
            else:
                remove_offline_services(onion)
                return HttpResponse(onion + ".onion is offline")
    elif request.method == 'GET':
        #is this http server been online within 7 days
        if hs.online:
            return HttpResponse("up")
        else:
            return HttpResponse("down")

def remove_offline_services(onion):
    """Remove those services that have not responsed within a week."""
    hs = HiddenWebsite.objects.get(id=onion)
    if hs.last_seen():
        # Test if hidden service has been online during this week
        # If it hasn't been online a week,
        # then it is officially offline
        days_seen = (datetime.now() - hs.last_seen()).days
        if days_seen >= 7:
            hs.online = False
            hs.full_clean()
            hs.save()

def fill_description(onion, title, keywords, description):
    """Fill description information if there are none."""
    hs = HiddenWebsite.objects.get(id=onion)
    hs.online = True
    hs.full_clean()
    hs.save()
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

def remove_historical_descriptions(hs):
    """Remove old descriptions."""
    descriptions = HiddenWebsiteDescription.objects.filter(about=hs)
    descriptions = descriptions.order_by('-updated')
    if len(descriptions) > 3:
        for desc in descriptions[3:]:
            desc.delete()

def add_info(json_data, onion):
    """Add the JSON description file."""
    json = simplejson.loads(json_data)
    not_official = json.get('not_official')
    if not_official:
        fill_description(onion, json.get("title"),
        json.get("keywords"), json.get("description"))
        message = "Description updated from " + onion + ".onion's HTML."
        return HttpResponse(message)
    else:
        add_official_info(json, onion)
        message = "Official description.json from " + onion + ".onion added."
        return HttpResponse(message)

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
    hs.online = True
    hs.full_clean()
    hs.save()
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
