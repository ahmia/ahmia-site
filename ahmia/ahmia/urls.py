"""The URL patterns of the ahmia."""
from django.conf import settings
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

# Root level views
urlpatterns = patterns(
    '',
    (r'^$', 'ahmia.views.default'), # search
    (r'^i2p/', 'ahmia.views.i2p_search'), # i2p search
    # legalese
    (r'^legal', 'ahmia.views.legal'),
    # Information about ahmia.
    (r'^about/', 'ahmia.views.about'),
    # Show visitor's IP address.
    (r'^IP/', 'ahmia.views.show_ip'),
    # Summer of Code 2014
    (r'^gsoc/', 'ahmia.views.gsoc'),
    # Banned services
    (r'^blacklist', 'ahmia.views.blacklist'),
    # Documentation page.
    (r'^documentation/', 'ahmia.views.documentation'),
)

# Documentation content
urlpatterns += patterns(
    '',
    # documentation/indexing
    (r'^documentation/indexing/', 'ahmia.views.indexing'),
    # Documentation - create hidden service description to hidden services.
    (r'^documentation/createHsDescription/',
     'ahmia.views.create_description'),
    # Documentation - description proposal to hidden services.
    (r'^documentation/descriptionProposal/',
     'ahmia.views.description_proposal'),
)

# Forms
urlpatterns += patterns(
    '',
    # Add domain form.
    (r'^add/', 'ahmia.views.add'), #domain:port/add
    # Blacklist reporting
    (r'^blacklist/report', 'ahmia.views.blacklist_report'),
)

# Rule views
urlpatterns += patterns(
    '',
    # Login and logout.
    (r'^rule/login/', 'ahmia.views.login'),
    (r'^rule/logout/', 'ahmia.views.logout'),
    # Rule content.
    (r'^rule/$', 'ahmia.views.rule'),
)

# include app urls
'''urlpatterns += patterns('',
                       url(r'^', include('search.urls')),
                       url(r'^', include('stats.url')),
                       url(r'^', include('api.url')))
)

# DEPRECATED ROUTES
urlpatterns += patterns(
    '',
    (r'^policy/', 'search.views.legacy.policy'),  # /blacklist
    (r'^disclaimer/', 'search.views.legacy.disclaimer'), # /legal
    (r'^banned/', 'search.views.legacy.banned'), # /blacklist/banned
    (r'^bannedMD5\.txt$', 'search.views.legacy.banned') # /blacklist/banned
)'''

# robots.txt file
urlpatterns += patterns(
    '',
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
                                               content_type='text/plain')),
)

# media files: CSS, JavaScript, images
if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^static/(?P<path>.*)$',
         'django.views.static.serve',
         {'document_root': settings.STATIC_ROOT}),
    )
