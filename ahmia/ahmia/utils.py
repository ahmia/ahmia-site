""" Utility fonctions """
from django.conf import settings
from django.utils import timezone
from elasticsearch import Elasticsearch


def get_elasticsearch_object():
    """ Creating an elasticsearch object to query the index """

    es_obj = Elasticsearch(hosts=settings.ELASTICSEARCH_SERVERS,
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
