"""
Views
Statistics: JSON data API and JavaScript viewers.
"""
from ahmia.models import TorStats
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


class UsageStatistics(CoreView):
    """Displays daily usage statistics"""
    template_name = "usage.html"

    # def get_context_data(self, **kwargs):
    #     """
    #     The template will not print the figures until we gather 3 days of data
    #     """
    #     kwargs = super(UsageStatistics, self).get_context_data(**kwargs)
    #     kwargs['num_days'] = len(TorStats.objects.month())
    #     return kwargs
