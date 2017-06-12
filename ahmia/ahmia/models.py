"""Models for the database of ahmia."""
import re
from validators import validate_onion_url, validate_status
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models

class HiddenWebsite(models.Model):
    """Hidden service website."""
    #for instance: http://3g2upl4pq6kufc4m.onion/
    onion = models.URLField(validators=[validate_onion_url, validate_status], unique=True)