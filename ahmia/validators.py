""" Validators used by forms and models. """
import re
from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings

def get_elasticsearch_client():
    """ Connection to the Elasticsearch index """
    return Elasticsearch(
        hosts=[settings.ELASTICSEARCH_SERVER],
        http_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
        ca_certs=settings.ELASTICSEARCH_CA_CERTS,
        timeout=settings.ELASTICSEARCH_TIMEOUT,
    )

def extract_domain_from_url(url):
    """ Removes protocol, subdomain and url path """
    try:
        domain = urlparse(url).netloc
        main_domain = '.'.join(domain.split('.')[-2:])
        return main_domain
    except:
        return None

def allowed_url(url):
    """Checks if the URL is allowed based on its domain."""
    allowed_domains = [
        'webropolsurveys.com',
        'pelastakaalapset.fi',
        'mielenterveystalo.fi',
        'iterapi.se',
        'troubled-desire.com'
    ]
    domain = extract_domain_from_url(url)
    if is_valid_onion(domain) or domain in allowed_domains:
        return True
    return False

def validate_status(value):
    """Test if an onion domain is not banned."""
    es = get_elasticsearch_client()
    response = es.search(
        index=settings.ELASTICSEARCH_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"term": {"domain.keyword": value}},  # .keyword for exact match in ES 7+
                        {"term": {"is_banned": True}}  # Assuming 'is_banned' is a boolean field
                    ]
                }
            }
        },
        size=0  # We're only interested in the count
    )
    # In Elasticsearch 7+, the count can be found in response['hits']['total']
    # in 7.10+ it could be an int
    total = response['hits']['total']
    count = total if isinstance(total, int) else total['value']
    if count > 0:
        raise ValidationError(_("This onion domain is banned and cannot be added to this index."))

def validate_onion_url(url):
    """
    Test is url correct onion URL.
    Must be like http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/
    """
    if not url:
        raise ValidationError(_('NoneType is not a valid url'))
    url = url.strip()

    if not url.startswith('http://') and not url.startswith('https://'):
        raise ValidationError(_(f"{url} url is not a valid onion url"))

    validate_onion(extract_domain_from_url(url))

def validate_onion(onion):
    """Test if a url is a valid hiddenservice domain"""
    if not onion.endswith('.onion'):
        raise ValidationError(_(f"{onion} is not a valid onion address"))
    main_onion_domain_part = onion.split('.')[-2]
    if not re.match(r'^[a-z2-7]{56}$', main_onion_domain_part):
        raise ValidationError(_(f"{onion} is not a valid onion address"))

def is_valid_onion_url(url):
    """Checks if the given URL is a valid onion URL."""
    try:
        validate_onion_url(url)
        return True
    except ValidationError:
        return False

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
