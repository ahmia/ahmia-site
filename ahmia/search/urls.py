"""The URL patterns of the ahmia search app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^search/', views.results), # results
    url(r'^i2p_search/', views.results), # results
]

# Elasticsearch API
urlpatterns += [
    url(r'^elasticsearch/', views.proxy),
]
