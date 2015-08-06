"""

Legacy Redirects
These are for deprecated routes.

"""
from django.http import HttpResponse, HttpResponseNotAllowed
from django.template import Context, loader
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import redirect

@require_GET
def policy(request):
    return redirect('/blacklist')

@require_GET
def banned(request):
    return redirect('/blacklist/banned')

@require_GET
def disclaimer(request):
    return redirect('/legal')
