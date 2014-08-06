# encoding: utf-8
"""Experimental Solr Grouping / Field Collapsing backend for Haystack 2.0"""
# NOTE: You must be running the latest Pysolr master - no PyPI release yet!
# See https://gist.github.com/3750774 for the current version of this code
# See http://wiki.apache.org/solr/FieldCollapsing for the Solr feature documentation
from __future__ import absolute_import

import logging

from django.db.models.loading import get_model

from haystack.backends import EmptyResults
from haystack.backends.solr_backend import (SolrEngine, SolrSearchBackend,
                                            SolrSearchQuery)
from haystack.constants import DJANGO_CT, DJANGO_ID, ID
from haystack.models import SearchResult
from haystack.query import SearchQuerySet


# Since there's no chance of this being portable (yet!) we'll import explicitly
# rather than using the generic imports:


class GroupedSearchQuery(SolrSearchQuery):

    def __init__(self, *args, **kwargs):
        super(GroupedSearchQuery, self).__init__(*args, **kwargs)
        self.grouping_field = None
        self._total_document_count = None

    def _clone(self, **kwargs):
        clone = super(GroupedSearchQuery, self)._clone(**kwargs)
        clone.grouping_field = self.grouping_field
        return clone

    def add_group_by(self, field_name):
        self.grouping_field = field_name

    def post_process_facets(self, results):
        # FIXME: remove this hack once https://github.com/toastdriven/django-haystack/issues/750 lands
        # See matches dance in _process_results below:
        total = 0

        if 'hits' in results:
            total = int(results['hits'])
        elif 'matches' in results:
            total = int(results['matches'])

        self._total_document_count = total

        return super(GroupedSearchQuery, self).post_process_facets(results)

    def get_total_document_count(self):
        """Return the total number of matching documents rather than document groups

        If the query has not been run, this will execute the query and store the results.
        """
        if self._total_document_count is None:
            self.run()

        return self._total_document_count

    def build_params(self, *args, **kwargs):
        res = super(GroupedSearchQuery, self).build_params(*args, **kwargs)
        if self.grouping_field is not None:
            res.update({'group': 'true',
                        'group.field': self.grouping_field,
                        'group.ngroups': 'true',
                        'group.limit': 2,  # TODO: Don't hard-code this
                        'group.sort': 'django_ct desc, score desc',
                        'group.facet': 'true',
                        'result_class': GroupedSearchResult})
        return res


class GroupedSearchResult(object):

    def __init__(self, field_name, group_data, raw_results={}):
        self.field_name = field_name
        self.key = group_data['groupValue']  # TODO: convert _to_python
        self.hits = group_data['doclist']['numFound']
        self.documents = list(self.process_documents(group_data['doclist']['docs'],
                                                     raw_results=raw_results))

    def __unicode__(self):
        return 'GroupedSearchResult({0.field_name}={0.group_key}, hits={0.hits})'.format(self)

    def process_documents(self, doclist, raw_results):
        # TODO: tame import spaghetti
        from haystack import connections
        engine = connections["default"]
        conn = engine.get_backend().conn

        unified_index = engine.get_unified_index()
        indexed_models = unified_index.get_indexed_models()

        for raw_result in doclist:
            app_label, model_name = raw_result[DJANGO_CT].split('.')
            additional_fields = {}
            model = get_model(app_label, model_name)

            if model and model in indexed_models:
                for key, value in raw_result.items():
                    index = unified_index.get_index(model)
                    string_key = str(key)

                    if string_key in index.fields and hasattr(index.fields[string_key], 'convert'):
                        additional_fields[string_key] = index.fields[string_key].convert(value)
                    else:
                        additional_fields[string_key] = conn._to_python(value)

                del(additional_fields[DJANGO_CT])
                del(additional_fields[DJANGO_ID])
                del(additional_fields['score'])

                if raw_result[ID] in getattr(raw_results, 'highlighting', {}):
                    additional_fields['highlighted'] = raw_results.highlighting[raw_result[ID]]

                result = SearchResult(app_label, model_name, raw_result[DJANGO_ID],
                                      raw_result['score'], **additional_fields)
                yield result


class GroupedSearchQuerySet(SearchQuerySet):

    def __init__(self, *args, **kwargs):
        super(GroupedSearchQuerySet, self).__init__(*args, **kwargs)

        if not isinstance(self.query, GroupedSearchQuery):
            raise TypeError("GroupedSearchQuerySet must be used with a GroupedSearchQuery query")

    def group_by(self, field_name):
        """Have Solr group results based on the provided field name"""
        clone = self._clone()
        clone.query.add_group_by(field_name)
        return clone

    def post_process_results(self, results):
        # Override the default model-specific processing
        return results

    def total_document_count(self):
        """Returns the count for the total number of matching documents rather than groups

        A GroupedSearchQuerySet normally returns the number of document groups; this allows
        you to indicate the total number of matching documents - quite handy for making facet counts match the
        displayed numbers
        """
        if self.query.has_run():
            return self.query.get_total_document_count()
        else:
            clone = self._clone()
            return clone.query.get_total_document_count()


class GroupedSolrSearchBackend(SolrSearchBackend):

    def build_search_kwargs(self, *args, **kwargs):
        group_kwargs = [(i, kwargs.pop(i)) for i in kwargs.keys() if i.startswith("group")]

        res = super(GroupedSolrSearchBackend, self).build_search_kwargs(*args, **kwargs)

        res.update(group_kwargs)
        if group_kwargs and 'sort' not in kwargs:
            res['sort'] = 'score desc'

        return res

    def _process_results(self, raw_results, result_class=None, **kwargs):
        res = super(GroupedSolrSearchBackend, self)._process_results(raw_results,
                                                                     result_class=result_class,
                                                                     **kwargs)

        if result_class and not issubclass(result_class, GroupedSearchResult):
            return res

        if len(raw_results.docs):
            raise RuntimeError("Grouped Solr searches should return grouped elements, not docs!")

        assert not res['results']
        assert not res['hits']

        if isinstance(raw_results, EmptyResults):
            return res

        assert len(raw_results.grouped) == 1, "Grouping on more than one field is not supported"

        res['results'] = results = []
        for field_name, field_group in raw_results.grouped.items():
            res['hits'] = field_group['ngroups']
            res['matches'] = field_group['matches']
            for group in field_group['groups']:
                if group['groupValue'] is None:
                    logging.warning("Unexpected NULL grouping", extra={'data': raw_results})
                    res['hits'] -= 1  # Avoid confusing Haystack with excluded bogon results
                    continue
                results.append(result_class(field_name, group, raw_results=raw_results))

        return res


class GroupedSolrEngine(SolrEngine):
    backend = GroupedSolrSearchBackend
    query = GroupedSearchQuery
