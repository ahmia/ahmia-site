"""The URL patterns of the ahmia search app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^', views.TorResultsView.as_view(), name="results"), # results
    url(r'^i2p/', views.IipResultsView.as_view(), name="results-i2p"), # results
    # Redirect link to hidden service
    url(r'^redirect/', views.OnionRedirectView.as_view(), name="redirect"),
]

# Elasticsearch API
'''urlpatterns += [
    url(r'^elasticsearch/', views.proxy),
]'''
