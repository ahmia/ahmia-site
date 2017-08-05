""" Validators used by forms and models. """

import re

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext as _

from .utils import get_elasticsearch_object

def validate_status(value):
    """Test if an onion domain is not banned."""

    res = get_elasticsearch_object().count(
        index=settings.ELASTICSEARCH_INDEX,
        doc_type=settings.ELASTICSEARCH_INDEX,
        body={
            "query": {
                "constant_score" : {
                    "filter" : {
                        "bool": {
                            "must": [
                                {"term": {"domain": value}},
                                {"term": {"banned": 1}}
                            ]
                        }
                    }
                }
            }
        }
    )
    if res['count'] > 0:
        raise ValidationError(
            _("This onion is banned and cannot be added to this index.")
        )

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
    main_dom = url.find('.')
    if main_dom == 23:
        main_dom = 6
    if not validate_onion(url[main_dom+1:-7]):
        raise ValidationError(
            _(u'%(url)s is not valid onion domain') % {'url': url}
        )

def validate_onion(url):
    """Test if an url is a valid hiddenservice url"""
    return re.match(r"^[a-z2-7]{16}(\.onion)?", url.strip())
