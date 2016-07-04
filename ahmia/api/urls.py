"""The URL patterns of the ahmia API."""
from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    # Check is domain up.
    # domain:port/address/3g2upl4pq6kufc4m/up
    (r'^address/([a-z2-7]{16})/status', 'api.views.test.onion_up'),
    # Edit information of a hidden service
    # domain:port/address/3g2upl4pq6kufc4m/edit
    (r'^address/([a-z2-7]{16})/edit', 'api.views.onion_edit'),
    # Popularity of a hidden service
    (r'^address/([a-z2-7]{16})/popularity', 'api.views.onion_popularity'),
    #/address/ API
    # domain:port/address/3g2upl4pq6kufc4m
    (r'^address/([a-z2-7]{16})', 'api.views.single_onion'),
    # All domains that are online and are not banned
    (r'^address/online', 'api.views.onions_online_txt'),
    # Invalid /address URL.
    (r'^address/(.+)', 'api.views.onion_error'),
    # GET lists every known HS and POST adds a new HS.
    # domain:port/address/
    (r'^address/', 'api.views.onion_list'),
    # Redirect link to hidden service
    (r'^redirect', 'api.views.onion_redirect'),
    # Banned hidden services (MD5).
    # The plain texts list of onion URL.
    (r'^onions/', 'api.views.onions_txt'),
    (r'^oniondomains\.txt$', 'api.views.onions_txt'),
    # Every onion domain. Including banned. Only for localhost.
    (r'^alldomains', 'api.views.all_onions_txt'),
    # Blacklist MD5
    (r'^blacklist/banned', 'api.views.banned'),
)
