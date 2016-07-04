"""The URL patterns of the ahmia stats app."""
from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    # Stats
    (r'^stats/viewer', 'stats.views.statsviewer'),
    (r'^stats/popularity', 'stats.views.stats'),
    (r'^stats/tor2web', 'stats.views.tor2web'),
    (r'^stats/history', 'stats.views.history'),
    (r'^stats/traffic', 'stats.views.trafficviewer'),
    (r'^stats/services', 'stats.views.services'),
    (r'^stats/onionsovertime', 'stats.views.onionsovertime'),
)
