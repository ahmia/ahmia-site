"""The URL patterns of the ahmia."""
from django.conf import settings
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.views.static import serve

from . import views

# Root level views
urlpatterns = [
    url(r'^$', views.default), # search
    url(r'^i2p/', views.i2p_search), # i2p search
    # legalese
    url(r'^legal', views.legal),
    # Information about ahmia.
    url(r'^about/', views.about),
    # Show visitor's IP address.
    url(r'^IP/', views.show_ip),
    # Summer of Code 2014
    url(r'^gsoc/', views.gsoc),
    # Documentation page.
    url(r'^documentation/', views.documentation),
    # Banned services
    url(r'^blacklist', views.blacklist),
]

# Documentation content
urlpatterns += [
    # documentation/indexing
    url(r'^documentation/indexing/', views.indexing),
    # Documentation - create hidden service description to hidden services.
    url(r'^documentation/createHsDescription/',
        views.create_description),
    # Documentation - description proposal to hidden services.
    url(r'^documentation/descriptionProposal/',
        views.description_proposal),
]

# Forms
urlpatterns += [
    # Add domain form.
    url(r'^add/', views.add), #domain:port/add
    # Blacklist reporting
    url(r'^blacklist/report', views.blacklist_report),
]

# include app urls
urlpatterns += [
    url(r'^', include('search.urls')),
    url(r'^', include('stats.urls')),
    url(r'^', include('api.urls'))
]

# robots.txt file
urlpatterns += [
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
                                               content_type='text/plain')),
]

# media files: CSS, JavaScript, images
if settings.DEBUG:
    urlpatterns += [
        url(
            r'^static/(?P<path>.*)$',
            serve,
            {'document_root': settings.STATIC_ROOT}
        ),
    ]
