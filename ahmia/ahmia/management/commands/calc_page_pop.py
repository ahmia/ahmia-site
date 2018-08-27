from django.core.management import BaseCommand
from elasticsearch.helpers import scan

from ahmia import utils
from ahmia.lib.pagepop import PagePopHandler


class Command(BaseCommand):
    help = 'Ranks Pages Based on PagePop algorithm found in ahmia/lib'

    def __init__(self):
        super(BaseCommand, self).__init__()

        self.es_obj = utils.get_elasticsearch_object()
        self.es_index = utils.get_elasticsearch_tor_index()

    def _fetch_all_docs(self):
        """Returns a generator to iterate all records"""
        doc_gen = scan(
            self.es_obj,
            query={"query": {"match_all": {}}},
            index=self.es_index,
            scroll='30m'
        )

        return doc_gen

    def handle(self, *args, **options):
        doc_gen = self._fetch_all_docs()

        p = PagePopHandler(documents=doc_gen, beta=0.85)
        p.build_pagescores()
        p.save()
