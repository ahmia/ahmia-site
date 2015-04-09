"""Models for the database of ahmia."""
import re

from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models


# Validators
def validate_onion_url(url):
    """ Test is url correct onion URL."""
    #Must be like http://3g2upl4pq6kufc4m.onion/
    if len(url) != 30:
        raise ValidationError(u'%s length is not 30' % url)
    if url[0:7] != 'http://':
        raise ValidationError(u'%s is not beginning with http://' % url)
    if url[-7:] != '.onion/':
        raise ValidationError(u'%s is not ending with .onion/' % url)
    if not re.match("[a-z2-7]{16}", url[7:-7]):
        raise ValidationError(u'%s is not valid onion domain' % url)

class HiddenWebsite(models.Model):
    """Hidden service website."""
    #for instance: http://3g2upl4pq6kufc4m.onion/
    url = models.URLField(validators=[validate_onion_url], unique=True)
    #hidden service
    id = models.CharField(primary_key=True, max_length=16,
    validators=[MinLengthValidator(16), MaxLengthValidator(16)], unique=True)
    #is this domain banned
    banned = models.BooleanField(default=False)
    #is it online or offline
    online = models.BooleanField(default=False)
    #echo -e "BLAHBLAHBLAH.onion\c" | md5sum
    #hashlib.md5(url[8:-1]).hexdigest()
    md5 = models.CharField(max_length=32,
    validators=[MinLengthValidator(32), MaxLengthValidator(32)], unique=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)
    class Meta:
        """Meta class."""
        app_label = 'ahmia'
    def __unicode__(self):
        return self.url

    def last_seen(self):
        """The datetime when the hidden service was last seen online"""
        try:
            return self.hiddenwebsitestatus_set.filter(online=True).latest('time').time
        except HiddenWebsiteStatus.DoesNotExist:
            return None

    def add_status(self, **kwargs):
        """Create a HiddenWebsiteStatus object for a hidden service
        
        Keyword arguments:
        time -- when the hidden service was tested (default=now)
        online -- whether the hidden service was found online (default=True)
        """
        self.hiddenwebsitestatus_set.create(**kwargs)

class HiddenWebsiteDescription(models.Model):
    """Hidden service website description."""
    about = models.ForeignKey(HiddenWebsite)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    relation = models.URLField(blank=True, null=True)
    subject = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)
    language = models.TextField(null=True, blank=True)
    contactInformation = models.TextField(null=True, blank=True)
    officialInfo = models.BooleanField(default=False)
    class Meta:
        """Meta class."""
        app_label = 'ahmia'
    def __unicode__(self):
        return self.about.url

class HiddenWebsitePopularity(models.Model):
    """Hidden service website popularity."""
    about = models.ForeignKey(HiddenWebsite)
    clicks = models.PositiveIntegerField(default=0, blank=True, null=True)
    public_backlinks = models.PositiveIntegerField(default=0, blank=True,
    null=True)
    tor2web = models.PositiveIntegerField(default=0, blank=True, null=True)
    class Meta:
        """Meta class."""
        app_label = 'ahmia'
    def __unicode__(self):
        return self.about.url

class HiddenWebsiteStatus(models.Model):
    """Hidden website online status"""
    about = models.ForeignKey(HiddenWebsite)
    time = models.DateTimeField(auto_now_add=True)
    online = models.BooleanField(default=True)
    def __unicode__(self):
        return self.about.url

class WebsiteIndex(models.Model):
    """Model for an indexed website."""
    domain = models.TextField()
    url = models.URLField(unique=True)
    tor2web_url = models.URLField(unique=True)
    text = models.TextField()
    title = models.TextField()
    h1 = models.TextField()
    h2 = models.TextField()
    crawling_session = models.TextField()
    server_header = models.TextField()
    date_inserted = models.DateTimeField()

    def __unicode__(self):
        return self.url
