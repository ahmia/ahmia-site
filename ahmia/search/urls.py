"""The URL patterns of the ahmia search app."""
from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    (r'^search/', 'search.views.results'), # results
    (r'^i2p_search/', 'search.views.results'), # results
)

# Elasticsearch API
urlpatterns += patterns(
    '',
    (r'^elasticsearch/', 'search.views.proxy'),
)
