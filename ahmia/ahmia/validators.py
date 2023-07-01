""" Validators used by forms and models. """

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from .utils import get_elasticsearch_object
from urllib.parse import urlparse

def extract_domain(url):
    ''' Returns the main domain from the URL address '''
    try:
        domain = urlparse(url).netloc
        main_domain = '.'.join(domain.split('.')[-2:])
        return main_domain
    except:
        return None

def allowed_url(redirect_url):
    """ Validate the URL as allowed redirect URL """
    allowed_domain_list = ['webropolsurveys.com', 'pelastakaalapset.fi', 'mielenterveystalo.fi', 'iterapi.se']
    main_domain = extract_domain(redirect_url)
    if not main_domain:
        return False
    # Specially allowed domains
    if main_domain in allowed_domain_list:
        return True
    # *.onion and *.i2p addresses
    if main_domain.split('.')[-1] == 'i2p' or main_domain.split('.')[-1] == 'onion':
        return True
    return False # Not allowed

def validate_status(value):
    """Test if an onion domain is not banned."""
    res = get_elasticsearch_object().count(
        index=settings.ELASTICSEARCH_TOR_INDEX,
        doc_type=settings.ELASTICSEARCH_TYPE,
        body={
            "query": {
                "constant_score": {
                    "filter": {
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


def validate_full_onion_url(url):
    """
    Check if an onion url represents a valid v2 or v3 onion url,
    with or without path. A valid url looks like:
    e.g: http://msydqstlz2kzerdg.onion/search/?q=tor+network&d=7

    :param url: The url in question
    :raises ValidationError
    :return: None
    """
    try:
        # check for trailing slash if there is a path
        path = url.split('.onion')[-1]
        if path and path[0] != '/':
            raise ValidationError(
                _("{} url path should start with '/'".format(url))
            )

        # check the rest of the url, left from .onion
        regex = "https?:\/\/([a-z0-9\-]+[.])*[a-z2-7]{16}([a-z2-7]{40})?[.]onion"
        if not re.match(regex, url.strip()):
            raise ValidationError(
                _("{} url is not a valid onion url".format(url))
            )
    except ValueError:
        # ValueError is parent to UnicodeError
        raise ValidationError(
            _("Url provided is invalid. It probably contains non-ascii "
              "characters that couldn't be encoded")
        )

# todo merge validate_full_onion_url() and validate_onion_url()


def validate_onion_url(url):
    """
    Test is url correct onion URL.
    Must be like http://3g2upl4pq6kufc4m.onion/
    """
    if not url:
        raise ValidationError(_('NoneType is not a valid url'))

    url = url.strip().rstrip('/')

    if url[0:7] != 'http://' and url[0:8] != 'https://':
        raise ValidationError(
            _(u'%(url)s is not beginning with http://') % {'url': url}
        )
    if url[-6:] != '.onion':
        raise ValidationError(
            _(u'%(url)s is not ending with .onion') % {'url': url}
        )

    # todo we should also validate subdomain
    main_dom = url.find('.')
    if main_dom in (23, 63):   # match both v2 & v3 lengths
        main_dom = 6

    validate_onion(url[main_dom+1:-6])


def validate_onion(onion):
    """Test if a url is a valid hiddenservice domain"""
    if not onion:
        raise ValidationError(_('The provided value is not a valid onion'))

    if not re.match(r"^[a-z2-7]{16}([a-z2-7]{40})?(\.onion)?$", onion.strip()):
        raise ValidationError(_("%s url is not a valid onion url" % onion))


def is_valid_onion_url(url):
    """
    Uses django validator validate_onion_url defined above
    in order to derive if url is a valid onion url, but
    returns boolean instead of throwing an exception

    :param url The url in question
    :returns True if valid onion_domain else False
    """
    try:
        validate_onion_url(url)
    except ValidationError:
        return False
    return True


def is_valid_full_onion_url(url):
    """
    Uses django validator validate_full_onion_url defined above
    but returns boolean instead of throwing an exception

    :param url The url in question
    :returns True if valid onion else False
    """
    try:
        validate_full_onion_url(url)
    except ValidationError:
        return False
    return True


def is_valid_onion(onion):
    """
    Uses django validate_onion defined above to validate onion
    but returns boolean instead of throwing an exception

    :param onion The onion in question
    :returns True if valid onion domain else False
    """
    try:
        validate_onion(onion)
    except ValidationError:
        return False
    return True
