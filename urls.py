"""The URL patterns of the ahmia."""

from django.conf.urls.defaults import *
from django.conf import settings

# For admin UI.
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Check is domain up.
    # domain:port/address/3g2upl4pq6kufc4m/up
    (r'^address/([a-z2-7]{16})/status', 'ahmia.views.onion_up'),
    # Edit information of a hidden service
    # domain:port/address/3g2upl4pq6kufc4m/edit
    (r'^address/([a-z2-7]{16})/edit/', 'ahmia.views.onion_edit'),
    #/address/ API
    # domain:port/address/3g2upl4pq6kufc4m
    (r'^address/([a-z2-7]{16})', 'ahmia.views.onion'),
    # Invalid /address URL.
    (r'^address/(.+)', 'ahmia.views.onion_error'),
    # GET lists every known HS and POST adds a new HS.
    # domain:port/address/
    (r'^address/', 'ahmia.views.onion_list'),
    # Login and logout.
    (r'^rule/login/', 'ahmia.views.login'),
    (r'^rule/logout/', 'ahmia.views.logout'),
    # Rule content.
    (r'^rule/$', 'ahmia.views.rule'),
    # Policy info.
    (r'^policy/', 'ahmia.views.policy'),
    # Disclaimer text.
    (r'^disclaimer/', 'ahmia.views.disclaimer'),
    # Documentation - create hidden service description to hidden services.
    (r'^documentation/createHsDescription/', 'ahmia.views.createHsDescription'),
    # Documentation - description proposal to hidden services.
    (r'^documentation/descriptionProposal/', 'ahmia.views.descriptionProposal'),
    # Banned hidden services (MD5).
    (r'^banned/', 'ahmia.views.banned'),
    # Documentation page.
    (r'^documentation/', 'ahmia.views.documentation'),
    # Information about ahmia.
    (r'^about/', 'ahmia.views.about'),
    # Information about Google Summer of Code 2014.
    (r'^gsoc/', 'ahmia.views.gsoc'),
    # Show visitor's IP address.
    (r'^IP/', 'ahmia.views.show_ip'),
    # The full text search page.
    (r'^search', 'ahmia.views.search_page'),
    # The full text search API.
    (r'^query', 'ahmia.views.query'),
    # Full text search using YaCy wrapper.
    #(r'^yacy/(.*)', 'ahmia.views.yacy_connection'),
    # Search without JavaScript: with XSLT.
    (r'^find/(.*)', 'ahmia.views.find'),
    # Site's admin UI.
    (r'^admin/', include(admin.site.urls)),
    # The plain texts list of onion URL.
    (r'^onions/', 'ahmia.views.onions_txt'),
    (r'^oniondomains\.txt$', 'ahmia.views.onions_txt'),
    # MD5 list of banned onion URLs.
    (r'^bannedMD5\.txt$', 'ahmia.views.banned'),
    # Plain texts list of banned onion URLs.
    (r'^banneddomains\.txt$', 'ahmia.views.banned_domains_plain'),
    # Every onion domain. Including banned. Only for localhost.
    (r'^alldomains', 'ahmia.views.all_onions_txt'),
    # favicon.ico
    (r'^favicon\.ico$', 'django.views.generic.base.RedirectView', {'url': '/static/images/favicon.ico'}),
    # Add domain form.
    (r'^add/', 'ahmia.views.add'), #domain:port/add
    (r'^$', 'ahmia.views.default'), #domain:port
)

#media files: CSS, JavaScript, images
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
