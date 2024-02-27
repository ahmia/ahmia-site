""" Models """
from django.db import models
from .validators import validate_onion_url, validate_status

class HiddenWebsite(models.Model):
    """ Hidden service website """
    onion = models.URLField(validators=[validate_onion_url, validate_status], unique=True)
    def __str__(self):
        return str(self.onion)
