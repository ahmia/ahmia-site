"""

Views
Statistics: JSON data API and JavaScript viewers.

"""
from ahmia.views import CoreView

class OnionsOverTimeView(CoreView):
    """Displays tor2web statitics of .onions over time"""
    template_name = "onions_over_time.html"
