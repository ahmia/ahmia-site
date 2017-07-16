"""

Views
Statistics: JSON data API and JavaScript viewers.

"""
from ahmia.views import CoreView

class Stats(CoreView):
    """Statisics Page"""
    template_name = "stats.html"

class LinkGraph(CoreView):
    """Visualizing Linking Graph"""
    template_name = "link_graph.html"

class OnionsOverTimeView(CoreView):
    """Displays tor2web statitics of .onions over time"""
    template_name = "onions_over_time.html"
