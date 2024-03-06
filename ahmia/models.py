""" Models """
from django.db import models
from .validators import validate_onion_url, validate_status, validate_onion

class HiddenWebsite(models.Model):
    """ Onion service website: http://xyz.onion/ """
    onion = models.URLField(validators=[validate_onion_url, validate_status], unique=True)
    def __str__(self):
        return str(self.onion)

class BannedWebsite(models.Model):
    """ Onion service website: xyz.onion """
    onion = models.CharField(max_length=255, unique=True, validators=[validate_onion])
    def __str__(self):
        return str(self.onion)
