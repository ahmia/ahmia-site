"""The URL patterns of the ahmia search app."""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^i2p/', views.IipResultsView.as_view(), name="results-i2p"),  # Results
    # Redirect to hidden service
    url(r'^search/redirect', views.onion_redirect),
    # This is the last
    url(r'^', views.TorResultsView.as_view(), name="results"),  # Results
]
