"""The URL patterns of the ahmia stats app."""
from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    # Stats
    (r'^stats/viewer', 'search.views.stats.statsviewer'),
    (r'^stats/popularity', 'search.views.stats.stats'),
    (r'^stats/tor2web', 'search.views.stats.tor2web'),
    (r'^stats/history', 'search.views.stats.history'),
    (r'^stats/traffic', 'search.views.stats.trafficviewer'),
    (r'^stats/services', 'search.views.stats.services'),
    (r'^stats/onionsovertime', 'search.views.stats.onionsovertime'),
)
