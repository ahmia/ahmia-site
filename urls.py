"""The URL patterns of the ahmia."""
from django.conf.urls import patterns, include
from django.conf import settings

# For admin UI.
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Check is domain up.
    # domain:port/address/3g2upl4pq6kufc4m/up
    (r'^address/([a-z2-7]{16})/status', 'views_online_test.onion_up'),
    # Edit information of a hidden service
    # domain:port/address/3g2upl4pq6kufc4m/edit
    (r'^address/([a-z2-7]{16})/edit', 'views.onion_edit'),
    # Popularity of a hidden service
    (r'^address/([a-z2-7]{16})/popularity', 'views.onion_popularity'),
    #/address/ API
    # domain:port/address/3g2upl4pq6kufc4m
    (r'^address/([a-z2-7]{16})', 'views.single_onion'),
    # All domains that are online and are not banned
    (r'^address/online', 'views.onions_online_txt'),
    # Invalid /address URL.
    (r'^address/(.+)', 'views.onion_error'),
    # GET lists every known HS and POST adds a new HS.
    # domain:port/address/
    (r'^address/', 'views.onion_list'),
    # Redirect link to hidden service
    (r'^redirect', 'views.onion_redirect'),
    # Banned hidden services (MD5).
    (r'^banned/', 'views.banned'),
    # The plain texts list of onion URL.
    (r'^onions/', 'views.onions_txt'),
    (r'^oniondomains\.txt$', 'views.onions_txt'),
    # MD5 list of banned onion URLs.
    (r'^bannedMD5\.txt$', 'views.banned'),
    # Plain texts list of banned onion URLs.
    (r'^banneddomains\.txt$', 'views.banned_domains_plain'),
    # Every onion domain. Including banned. Only for localhost.
    (r'^alldomains', 'views.all_onions_txt'),
    # Add domain form.
    (r'^add/', 'views.add'), #domain:port/add
    (r'^$', 'views_search.default'), #domain:port
)

# Search views
urlpatterns += patterns('',
    # The full text search page.
    (r'^search/', 'views_search.search_page'),
    # Search without JavaScript: with XSLT.
    (r'^find/(.*)', 'views_search.find'),
)

# Stats views
urlpatterns += patterns('',
    # Stats
    (r'^stats/viewer', 'views_stats.statsviewer'),
    (r'^stats/popularity', 'views_stats.stats'),
    (r'^stats/traffic', 'views_stats.trafficviewer')
)

# Admin views
urlpatterns += patterns('',
    # Site's admin UI.
    (r'^admin/', include(admin.site.urls)),
    # Login and logout.
    (r'^rule/login/', 'views_admin.login'),
    (r'^rule/logout/', 'views_admin.logout'),
    # Rule content.
    (r'^rule/$', 'views_admin.rule')
)

# From views_static
urlpatterns += patterns('',
    # Policy info.
    (r'^policy/', 'views_static.policy'),
    # Disclaimer text.
    (r'^disclaimer/', 'views_static.disclaimer'),
    (r'^documentation/indexing/', 'views_static.indexing'),
    # Documentation - create hidden service description to hidden services.
    (r'^documentation/createHsDescription/',
    'views_static.create_description'),
    # Documentation - description proposal to hidden services.
    (r'^documentation/descriptionProposal/',
    'views_static.description_proposal'),
    # Documentation page.
    (r'^documentation/', 'views_static.documentation'),
    # Information about ahmia.
    (r'^about/', 'views_static.about'),
    # Information about Google Summer of Code 2014.
    (r'^gsoc/', 'views_static.gsoc'),
    # Show visitor's IP address.
    (r'^IP/', 'views_static.show_ip')
)

#media files: CSS, JavaScript, images
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),
        # Full text search using YaCy wrapper.
        (r'^yacy/(.*)', 'views_search.yacy_connection'),
    )
