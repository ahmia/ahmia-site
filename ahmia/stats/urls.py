"""The URL patterns of the ahmia stats app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    # Stats
    url(r'^stats/viewer', views.statsviewer),
    url(r'^stats/popularity', views.stats),
    url(r'^stats/tor2web', views.tor2web),
    url(r'^stats/history', views.history),
    url(r'^stats/traffic', views.trafficviewer),
    url(r'^stats/services', views.services),
    url(r'^stats/onionsovertime', views.onionsovertime),
]
