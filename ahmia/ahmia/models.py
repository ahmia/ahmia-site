"""Models for the database of ahmia."""
from django.db import models
from django.core.validators import MaxLengthValidator, MinLengthValidator

class HiddenWebsite(models.Model):
    """Hidden service website."""
    #for instance: http://3g2upl4pq6kufc4m.onion/
    url = models.URLField(unique=True)
    #hidden service
    id = models.CharField(primary_key=True, max_length=16,
                          validators=[MinLengthValidator(16),
                                      MaxLengthValidator(16)],
                          unique=True)
    #is this domain banned
    banned = models.BooleanField(default=False)
    #is it online or offline
    online = models.BooleanField(default=False)
    #echo -e "BLAHBLAHBLAH.onion\c" | md5sum
    #hashlib.md5(url[8:-1]).hexdigest()
    md5 = models.CharField(max_length=32,
                           validators=[MinLengthValidator(32),
                                       MaxLengthValidator(32)],
                           unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    '''class Meta:
        """Meta class."""
        app_label = 'search'''
    def __unicode__(self):
        return self.url

    def last_seen(self):
        """The datetime when the hidden service was last seen online"""
        try:
            return self.hiddenwebsitestatus_set.filter(online=True) \
                                               .latest('time').time
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
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    language = models.TextField(null=True, blank=True)
    contactInformation = models.TextField(null=True, blank=True)
    officialInfo = models.BooleanField(default=False)
    '''class Meta:
        """Meta class."""
        app_label = 'ahmia'''
    def __unicode__(self):
        return self.about.url

class HiddenWebsitePopularity(models.Model):
    """Hidden service website popularity."""
    about = models.ForeignKey(HiddenWebsite)
    clicks = models.PositiveIntegerField(default=0, blank=True, null=True)
    public_backlinks = models.PositiveIntegerField(default=0, blank=True,
                                                   null=True)
    tor2web = models.PositiveIntegerField(default=0, blank=True, null=True)
    '''class Meta:
        """Meta class."""
        app_label = 'ahmia'''
    def __unicode__(self):
        return self.about.url

class HiddenWebsiteStatus(models.Model):
    """Hidden website online status"""
    about = models.ForeignKey(HiddenWebsite)
    time = models.DateTimeField(auto_now_add=True)
    online = models.BooleanField(default=True)
    def __unicode__(self):
        return self.about.url
