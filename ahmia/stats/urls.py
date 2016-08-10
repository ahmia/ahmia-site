"""The URL patterns of the ahmia stats app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^onionsovertime/', views.OnionsOverTimeView.as_view(),
        name="onionsovertime"),
]
