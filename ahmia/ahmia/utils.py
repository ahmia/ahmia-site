""" Utility fonctions """
from django.conf import settings
from elasticsearch import Elasticsearch


def get_elasticsearch_object():
    """ Creating an elasticsearch object to query the index """
    # todo move the default values to settings instead of using exception handling

    try:
        es_servers = settings.ELASTICSEARCH_SERVERS
        es_servers = es_servers if isinstance(es_servers, list) \
            else [es_servers]
    except AttributeError:
        es_servers = [settings.ELASTICSEARCH_SERVERS]

    try:
        timeout = settings.ELASTICSEARCH_TIMEOUT
    except AttributeError:
        timeout = 60
    es_obj = Elasticsearch(hosts=es_servers,
                           timeout=timeout)
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
