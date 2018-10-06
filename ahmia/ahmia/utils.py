""" Utility fonctions used by all apps """

from django.conf import settings
from django.utils import timezone
from elasticsearch import Elasticsearch


def get_elasticsearch_object():
    """ Creating an elasticsearch object to query the index """

    es_obj = Elasticsearch(
        hosts=settings.ELASTICSEARCH_SERVERS,
        timeout=settings.ELASTICSEARCH_TIMEOUT)
    return es_obj


def get_elasticsearch_both_index():
    """ Getting the name of the index """
    return settings.ELASTICSEARCH_BOTH_INDEX


def get_elasticsearch_tor_index():
    """ Getting the name of the index """
    return settings.ELASTICSEARCH_TOR_INDEX


def get_elasticsearch_i2p_index():
    """ Getting the name of the index """
    return settings.ELASTICSEARCH_I2P_INDEX


def get_elasticsearch_type():
    """ Getting the name of the main type used """
    return settings.ELASTICSEARCH_TYPE


def timezone_today():
    """ Timezone aware function that returns the current day"""
    return timezone.now().date()


def extract_domain_from_url(url):
    """
    Removes protocol, subdomain and url path. It does not
    perform any validation on input parameter url

    :param url Full onion url as str
    :return domain name as str
    """
    if '.onion' not in url:
        return None

    no_path_no_tld = url.split('.onion')[0]
    domain_name = no_path_no_tld.split('.')[-1].split('/')[-1]
    domain = domain_name + '.onion'

    return domain


def normalize_on_max(scalars):
    """
    Normalize ``scallars`` to have max value: 1
    Also substitudes None Values with a value a bit lower that min.

    :param scalars: Python iterable (not numpy)
    :return: A normalized version of input
    """
    max_i = max(i for i in scalars if i is not None)
    min_i = min(i for i in scalars if i is not None)
    class_type = type(scalars)

    # Substitude Nones with a value lower than min
    ret = [i if i else min_i / 3 for i in scalars]

    # normalize to max=1, return same type to scalars
    ret = class_type(i / max_i for i in ret)

    return ret
