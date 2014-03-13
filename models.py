from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re


####################### validators


#test is url correct onion url
#Must be like http://3g2upl4pq6kufc4m.onion/
def validate_onion_URL( url ):
    if len(url) != 30:
        raise ValidationError(u'%s length is not 30' % url)
    if url[0:7] != 'http://':
        raise ValidationError(u'%s is not beginning with http://' % url)
    if url[-7:] != '.onion/':
        raise ValidationError(u'%s is not ending with .onion/' % url)
    if not re.match( "[a-z2-7]{16}", url[7:-7] ):
	raise ValidationError(u'%s is not valid onion domain' % url)


#Test that length of the string is 32
def validate_length_32( string ):
    length = 32
    if len(string) != length:
        raise ValidationError(u'%s length is not %d' % (string, length) )


#Test that length of the string is 16
def validate_length_16( string ):
    length = 16
    if len(string) != length:
        raise ValidationError(u'%s length is not %d' % (string, length) )


#Test that length of the string is 2
def validate_length_2( string ):
    length = 2
    if len(string) != length:
        raise ValidationError(u'%s length is not %d' % (string, length) )


####################### models


#hidden service website
class HiddenWebsite(models.Model):
    #for instance: http://3g2upl4pq6kufc4m.onion/
    url = models.URLField( validators=[validate_onion_URL], unique=True )
    #hidden service
    id = models.CharField( primary_key=True, max_length=16, validators=[validate_length_16], unique=True )
    #is this domain banned
    banned = models.BooleanField()
    #is it online or offline
    seenOnline = models.DateTimeField(blank=True, null=True)
    online = models.BooleanField()
    #echo -e "BLAHBLAHBLAH.onion\c" | md5sum
    #hashlib.md5(url[8:-1]).hexdigest()
    md5 = models.CharField( max_length=32, validators=[validate_length_32], unique=True )
    updated = models.DateTimeField( auto_now=True, auto_now_add=True )
    def __unicode__(self):
    	return self.url


#hidden service website description
class HiddenWebsiteDescription(models.Model):
    about = models.ForeignKey( HiddenWebsite )
    title = models.TextField( blank=True, null=True )
    description = models.TextField( blank=True, null=True )
    relation = models.URLField( blank=True, null=True )
    subject = models.TextField( blank=True, null=True )
    type = models.TextField( blank=True, null=True )
    updated = models.DateTimeField( auto_now=True, auto_now_add=True )
    language = models.TextField( null=True, blank=True )
    contactInformation = models.TextField( null=True, blank=True )
    officialInfo = models.BooleanField()
    def __unicode__(self):
        return self.about.url


