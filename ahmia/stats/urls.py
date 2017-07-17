"""The URL patterns of the ahmia stats app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.Stats.as_view(), name="stats"),
    url(r'^link_graph/', views.LinkGraph.as_view(), name="link_graph"),
    url(r'^onionsovertime/', views.OnionsOverTimeView.as_view(), name="onionsovertime"),
]
