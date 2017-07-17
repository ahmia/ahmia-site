"""The URL patterns of the ahmia stats app."""
import os
from . import views
from django.conf.urls import url
from django.views.static import serve

urlpatterns = [
    url(r'^$', views.Stats.as_view(), name="stats"),
    url(r'^link_graph/', views.LinkGraph.as_view(), name="link_graph"),
    url(r'^onionsovertime/', views.OnionsOverTimeView.as_view(), name="onionsovertime"),
]

# static files: CSS, JavaScript, images
urlpatterns += [
    url(
        r'^static/(?P<path>.*)$',
        serve,
        {'document_root': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')}
    )
]
