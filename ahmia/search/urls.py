"""The URL patterns of the ahmia search app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^', views.results), # results
    url(r'^i2p/', views.results), # results
    # Redirect link to hidden service
    url(r'^redirect/', views.onion_redirect),
]

# Elasticsearch API
urlpatterns += [
    url(r'^elasticsearch/', views.proxy),
]
