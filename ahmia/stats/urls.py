"""The URL patterns of the ahmia stats app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    # Stats
    url(r'^viewer', views.statsviewer),
    url(r'^popularity', views.stats),
    url(r'^tor2web', views.tor2web),
    url(r'^history', views.history),
    url(r'^traffic', views.trafficviewer),
    url(r'^services', views.services),
    url(r'^onionsovertime', views.onionsovertime),
]
