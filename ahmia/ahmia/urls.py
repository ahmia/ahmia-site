"""The URL patterns of the ahmia."""
from django.conf import settings
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.views.static import serve

from . import views

# Root level views
urlpatterns = [
    url(r'^$', views.HomepageView.as_view(), name="home"),
    url(r'^i2p/', views.IipView.as_view(), name="i2p"),
    url(r'^legal/', views.LegalView.as_view(), name="legal"),
    url(r'^about/', views.AboutView.as_view(), name="about"),
    # Summer of Code 2014
    url(r'^gsoc/', views.GsocView.as_view(), name="gsoc"),
    # Documentation page.
    url(r'^documentation/$', views.DocumentationView.as_view(), name="doc"),
    # documentation/indexing
    url(r'^documentation/indexing/',
        views.IndexingDocumentationView.as_view(), name="doc-indexing"),
    # Documentation - create hidden service description to hidden services.
    url(r'^documentation/createHsDescription/',
        views.CreateDescDocumentationView.as_view(), name="doc-create-desc"),
    # Documentation - description proposal to hidden services.
    url(r'^documentation/descriptionProposal/',
        views.DescPropDocumentationView.as_view(), name="doc-desc-proposal"),
    # Banned services
    url(r'^blacklist/', views.BlacklistView.as_view(), name="blacklist"),
    # Add domain form.
    url(r'^add/', views.AddView.as_view(), name="add"), #domain:port/add
    # Blacklist reporting form
    url(r'^report/', views.ReportView.as_view(), name="report")
]

# include app urls
'''urlpatterns += [
    url(r'^search/', include('search.urls')),
    url(r'^stats/', include('stats.urls')),
    url(r'^api/', include('api.urls'))
]'''

# static files: CSS, JavaScript, images

urlpatterns += [
    url(
        r'^static/(?P<path>.*)$',
        serve,
        {'document_root': settings.STATIC_ROOT}
    ),
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
                                               content_type='text/plain')),
]
