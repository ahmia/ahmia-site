"""The URL patterns of the ahmia."""
from django.conf import settings
from django.conf.urls import url, include
from django.views.generic import TemplateView, RedirectView
from django.views.static import serve
from django.views.decorators.cache import cache_page

from . import views

# Root level views
urlpatterns = [
    url(r'^$', views.HomepageView.as_view(), name="home"),
    url(r'^i2p/', views.InvisibleInternetView.as_view(), name="i2p"),
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
    url(r'^blacklist/$', views.BlacklistView.as_view(), name="blacklist"),
    url(r'^blacklist/success/', views.BlacklistSuccessView.as_view(),
        name="blacklist-success"),
    url(r'^blacklist/banned/', cache_page(60 * 60)(views.BannedDomainListView.as_view()),
        name="domains-banned"),
    # Add domain form.
    url(r'^add/$', views.AddView.as_view(), name="add"), #domain:port/add
    url(r'^add/success/', views.AddSuccessView.as_view(), name="add-success"),
    # The plain texts list of onion URL.
    url(r'^onions/$', cache_page(60 * 60)(views.OnionListView.as_view()), name="onions"),
    # GET lists every known HS
    url(r'^address/$', cache_page(60 * 60)(views.AddressListView.as_view()), name="address"),
]

# deprecated urls
urlpatterns += [
    url(r'^disclaimer/',
        RedirectView.as_view(url="/legal/", permanent=True),
        name="disclaimer"),
    url(r'^banned/',
        RedirectView.as_view(url="/blacklist/banned/", permanent=True),
        name="banned"),
    url(r'^policy/',
        RedirectView.as_view(url="/blacklist/", permanent=True),
        name="policy"),
    url(r'^i2p_search/',
        RedirectView.as_view(url="/search/i2p/", permanent=True),
        name="i2p-old")
]

# include app urls
urlpatterns += [
    url(r'^search/', include('search.urls', namespace='search')),
    url(r'^stats/', include('stats.urls', namespace="api"))
]

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
