"""The URL patterns of the ahmia."""
from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    # Check is domain up.
    # domain:port/address/3g2upl4pq6kufc4m/up
    (r'^address/([a-z2-7]{16})/status', 'search.views.test.onion_up'),
    # Edit information of a hidden service
    # domain:port/address/3g2upl4pq6kufc4m/edit
    (r'^address/([a-z2-7]{16})/edit', 'search.views.onion_edit'),
    # Popularity of a hidden service
    (r'^address/([a-z2-7]{16})/popularity', 'search.views.onion_popularity'),
    #/address/ API
    # domain:port/address/3g2upl4pq6kufc4m
    (r'^address/([a-z2-7]{16})', 'search.views.single_onion'),
    # All domains that are online and are not banned
    (r'^address/online', 'search.views.onions_online_txt'),
    # Invalid /address URL.
    (r'^address/(.+)', 'search.views.onion_error'),
    # GET lists every known HS and POST adds a new HS.
    # domain:port/address/
    (r'^address/$', 'search.views.onion_list'),
    # Redirect link to hidden service
    (r'^redirect', 'search.views.onion_redirect'),
    # Banned hidden services (MD5).
    # The plain texts list of onion URL.
    (r'^onions/', 'search.views.onions_txt'),
    (r'^oniondomains\.txt$', 'search.views.onions_txt'),
    # Add domain form.
    (r'^add/', 'search.views.add'), #domain:port/add
    (r'^i2p/', 'search.views.searchengine.i2p_search'), # i2p search
    (r'^search/', 'search.views.searchengine.results'), # results
    (r'^i2p_search/', 'search.views.searchengine.results'), # results
    (r'^$', 'search.views.searchengine.default') #domain:port
)

# Elasticsearch API
urlpatterns += patterns(
    '',
    (r'^elasticsearch/', 'search.views.searchengine.proxy'),
)

# Stats views
urlpatterns += patterns(
    '',
    # Stats
    (r'^stats/viewer', 'search.views.stats.statsviewer'),
    (r'^stats/popularity', 'search.views.stats.stats'),
    (r'^stats/tor2web', 'search.views.stats.tor2web'),
    (r'^stats/history', 'search.views.stats.history'),
    (r'^stats/traffic', 'search.views.stats.trafficviewer'),
    (r'^stats/services', 'search.views.stats.services'),
    (r'^stats/onionsovertime', 'search.views.stats.onionsovertime'),
)

# Rule views
urlpatterns += patterns(
    '',
    # Login and logout.
    (r'^rule/login/', 'search.views.admin.login'),
    (r'^rule/logout/', 'search.views.admin.logout'),
    # Rule content.
    (r'^rule/$', 'search.views.admin.rule'),
)


# From views_static
urlpatterns += patterns(
    '',
    # Every onion domain. Including banned. Only for localhost.
    (r'^alldomains', 'search.views.all_onions_txt'),
    # Blacklist MD5
    (r'^blacklist/banned', 'search.views.banned'),
    # Blacklist reporting
    (r'^blacklist/report', 'search.views.blacklist_report'),
    # Banned services
    (r'^blacklist$', 'search.views.blacklist'),
    # legalese
    (r'^legal', 'search.views.static.legal'),
    # documentation/indexing
    (r'^documentation/indexing/', 'search.views.static.indexing'),
    # Documentation - create hidden service description to hidden services.
    (r'^documentation/createHsDescription/',
     'search.views.static.create_description'),
    # Documentation - description proposal to hidden services.
    (r'^documentation/descriptionProposal/',
     'search.views.static.description_proposal'),
    # Documentation page.
    (r'^documentation/$', 'search.views.static.documentation'),
    # Information about ahmia.
    (r'^about/', 'search.views.static.about'),
    # Show visitor's IP address.
    (r'^IP/', 'search.views.static.show_ip'),
    # Summer of Code 2014
    (r'^gsoc/', 'search.views.static.gsoc'),
)

# DEPRECATED ROUTES
urlpatterns += patterns(
    '',
    (r'^policy/', 'search.views.legacy.policy'),
    (r'^disclaimer/', 'search.views.legacy.disclaimer'),
    (r'^banned/', 'search.views.legacy.banned'),
    (r'^bannedMD5\.txt$', 'search.views.legacy.banned')
)
