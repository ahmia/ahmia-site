"""The URL patterns of the ahmia API."""
from django.conf.urls import url

from . import views

urlpatterns = [
    # Check is domain up.
    # domain:port/address/3g2upl4pq6kufc4m/up
    # url(r'^address/([a-z2-7]{16})/status', views.test.onion_up),
    # Edit information of a hidden service
    # domain:port/address/3g2upl4pq6kufc4m/edit
    url(r'^address/([a-z2-7]{16})/edit', views.onion_edit),
    # Popularity of a hidden service
    url(r'^address/([a-z2-7]{16})/popularity', views.onion_popularity),
    #/address/ API
    # domain:port/address/3g2upl4pq6kufc4m
    url(r'^address/([a-z2-7]{16})', views.single_onion),
    # All domains that are online and are not banned
    url(r'^address/online', views.onions_online_txt),
    # Invalid /address URL.
    url(r'^address/(.+)', views.onion_error),
    # GET lists every known HS and POST adds a new HS.
    # domain:port/address/
    url(r'^address/', views.onion_list),
    # Banned hidden services (MD5).
    # The plain texts list of onion URL.
    url(r'^onions/', views.onions_txt),
    url(r'^oniondomains\.txt$', views.onions_txt),
    # Every onion domain. Including banned. Only for localhost.
    url(r'^alldomains', views.all_onions_txt),
    # Blacklist MD5
    url(r'^blacklist/banned', views.banned),
    # Show visitor's IP address.
    url(r'^ip/', views.show_ip),
]
