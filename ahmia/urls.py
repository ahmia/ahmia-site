"""
URL configuration for ahmia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, RedirectView
from django.views.static import serve
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.HomepageView.as_view(), name='home'),
    path('legal/', views.LegalView.as_view(), name='legal'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('documentation/', views.DocumentationView.as_view(), name='doc'),
    path('documentation/indexing/', views.IndexingDocumentationView.as_view(),
                                    name='doc-indexing'),
    path('blacklist/', views.BlacklistView.as_view(), name='blacklist'),
    path('blacklist/banned/', cache_page(60 * 60)(views.BannedDomainListView.as_view()),
        name='domains-banned'),
    path('banned/', RedirectView.as_view(url="/blacklist/banned/", permanent=True),
        name='banned'),
    path('add/', views.AddView.as_view(), name='add'),
    path('add/onionsadded/', views.AddListView.as_view(), name='onions-added'),
    path('onions/', cache_page(60 * 60)(views.OnionListView.as_view()), name='onions'),
    path('address/', cache_page(60 * 60)(views.AddressListView.as_view()), name='address'),
    path('search/redirect', views.onion_redirect, name="onion-redirect"),
    path('search/', views.TorResultsView.as_view(), name="results"),
    #re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
                                                   content_type='text/plain')),
]
