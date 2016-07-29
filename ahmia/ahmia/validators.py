""" Validators used by forms and models. """

import re

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext as _

def validate_status(value):
    """Test if an onion domain is not banned."""
    try:
        raise ValidationError(
            _("This onion is banned and cannot be added to this index.")
        )
    except ObjectDoesNotExist:
        pass

def validate_onion_url(url):
    """ Test is url correct onion URL."""
    #Must be like http://3g2upl4pq6kufc4m.onion/
    if url[0:7] != 'http://':
        raise ValidationError(
            _(u'%(url)s is not beginning with http://') % {'url': url}
        )
    if url[-7:] != '.onion/':
        raise ValidationError(
            _(u'%(url)s is not ending with .onion/') % {'url': url}
        )
    if not validate_onion(url[7:-7]):
        raise ValidationError(
            _(u'%(url)s is not valid onion domain') % {'url': url}
        )

def validate_onion(url):
    """Test if an url is a valid hiddenservice url"""
    return re.match(r"^[a-z2-7]{16}(\.onion)?", url.strip())
