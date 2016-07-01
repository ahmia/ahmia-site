"""The URL patterns of the ahmia search app."""
from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    (r'^search/', 'search.views.searchengine.results'), # results
    (r'^i2p_search/', 'search.views.searchengine.results'), # results
)

# Elasticsearch API
urlpatterns += patterns(
    '',
    (r'^elasticsearch/', 'search.views.searchengine.proxy'),
)
