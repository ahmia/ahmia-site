"""

Legacy Redirects
These are for deprecated routes.

"""
from django.views.decorators.http import require_GET
from django.shortcuts import redirect

@require_GET
def policy(request):
    """Redirect former policy page to blacklist."""
    return redirect('/blacklist')

@require_GET
def banned(request):
    """Redirect former banned page."""
    return redirect('/blacklist/banned')

@require_GET
def disclaimer(request):
    """Redirect former disclaimer page to /legal."""
    return redirect('/legal')
