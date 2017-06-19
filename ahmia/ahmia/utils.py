""" Utility fonctions """
from elasticsearch import Elasticsearch

from django.conf import settings

def get_elasticsearch_object():
    """ Creating an elasticsearch object to query the index """
    try:
        es_servers = settings.ELASTICSEARCH_SERVERS
        es_servers = es_servers if isinstance(es_servers, list) \
            else [es_servers]
    except AttributeError:
        es_servers = ["http://localhost:9200"]#["https://ahmia.fi/esconnection/"]

    try:
        timeout = settings.ELASTICSEARCH_TIMEOUT
    except AttributeError:
        timeout = 60
    es_obj = Elasticsearch(hosts=es_servers,
                           timeout=timeout)
    return es_obj

def get_elasticsearch_index():
    """ Getting the name of the index """
    return settings.ELASTICSEARCH_INDEX

def get_elasticsearch_type():
    """ Getting the name of the main type used """
    return settings.ELASTICSEARCH_TYPE
