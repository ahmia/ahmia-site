"""Models for the database of ahmia."""
from django.db import models

from .validators import validate_onion_url, validate_status


class HiddenWebsite(models.Model):
    """Hidden service website."""
    # For instance: http://3g2upl4pq6kufc4m.onion/
    onion = models.URLField(validators=[validate_onion_url, validate_status], unique=True)


class SearchResultsClicks(models.Model):
    onionDomain = models.URLField(validators=[validate_onion_url])
    clicked = models.URLField()
    searchTerm = models.CharField(max_length=64)
