import itertools
import logging

import numpy as np
from scipy import sparse

from ahmia import utils
from ahmia.models import PagePopScore, PagePopStats
from ahmia.validators import is_valid_full_onion_url, is_valid_onion

logger = logging.getLogger('ahmia')


class PagePopHandler(object):

    def __init__(self, documents=None, beta=0.85, epsilon=10 ** -6):
        """
        Handler for PagePop algorithm. It uses a :dict: `domain_idxs` in
        order to assign each domain an id, that's the corresponding
        index to `scores`, list, that hold the pagepop scores.
        ``self.num_domains`` is used as  a counter while building
        adjacency matrix and ``domain_idxs`` is also stored as an
        instance attribute for statistics purposes.

        :param documents: An iterable to fetch documents from. It should be a
            generator in order to reduce memory used.
        :param beta: 1-teleportation probability.
        :param epsilon: stop condition. Minimum allowed amount of change
            in the PagePops between iterations.
        """
        self.documents = documents
        self.beta = beta
        self.epsilon = epsilon

        self.domains_idxs = {}
        self.scores = None

        self.num_domains = 0
        self.num_links = None
        self.num_edges = None

    def _get_domain_idx(self, domain):
        domain_idxs = self.domains_idxs

        if domain not in domain_idxs:
            domain_idxs[domain] = self.num_domains
            self.num_domains += 1

        return domain_idxs[domain]

    def _store_page_pop_stats(self):
        kwargs = self.get_stats()

        _, _ = PagePopStats.objects.update_or_create(
            day=utils.timezone_today(),
            defaults=kwargs)

    def get_stats(self):
        """
        Return number of domains (nodes), links (total links),
        edges (unique inter-site links) as a dict

        :rtype: ``dict``
        """
        ret = {
            'num_nodes': self.num_domains,
            'num_links': self.num_links,
            'num_edges': self.num_edges
        }

        return ret

    def build_adjacency_graph(self, documents):
        """
        Constructs adjacency graph for outgoing links, saves to self.adj_graph

        :param documents: An iterable that contains the ES documents.
            Preferably a generator to reduce RAM usage.
        :return: adjacency matrix
        :rtype: ``list`` of tuples
        """
        documents = documents or self.documents
        adj_graph = []

        for doc in documents:
            source = doc['_source']

            if 'domain' in source:
                origin = source['domain']
            elif 'source' in source:
                origin = source['source']
            else:
                logger.info('rank_pages: Unable to process: %s' % source)
                continue

            origin = utils.extract_domain_from_url(origin)
            if is_valid_onion(origin):
                origin_idx = self._get_domain_idx(origin)

                links = source.get('links', [])  # domain case
                if 'target' in source:           # source case
                    links.append({'link': source['target']})
                for l in links:
                    url = l['link']
                    if is_valid_full_onion_url(url):
                        destiny = utils.extract_domain_from_url(url)
                        if destiny != origin:
                            destiny_idx = self._get_domain_idx(destiny)
                            adj_graph.append((origin_idx, destiny_idx))

        self.num_links = len(adj_graph)  # total links
        adj_graph = set(adj_graph)  # count only 1 edge of source->destiny
        self.num_edges = len(adj_graph)  # unique links

        return adj_graph

    def build_sparse_matrix(self, adj_graph, num_nodes=None):
        """
        Builds a sparse matrix needed by compute_page_pop()

        :param adj_graph: A directed adjacency pragh as an iterable structure
        :param num_nodes: The number of nodes referenced in adj_graph
        :return: A sparse boolean matrix representing a link map
        :rtype: ``scipy.sparse.csr.csr_matrix``
        """
        num_nodes = num_nodes or self.num_domains

        row = [edge[1] for edge in adj_graph]  # destinies
        col = [edge[0] for edge in adj_graph]  # origins

        # if number of nodes not supplied count distinctly the nodes
        num_nodes = num_nodes or len(set(itertools.chain(row, col)))
        # print("nodes counted: %s" % len(set(itertools.chain(row, col))))

        return sparse.csr_matrix(
            ([True] * len(adj_graph), (row, col)),
            shape=(num_nodes, num_nodes))

    def compute_page_pop(self, adj, beta=None, epsilon=None):
        """
        Efficient computation of the PagePop values using a sparse adjacency
        matrix and the iterative power method.
        based on https://is.gd/weFAC1 (blog.samuelmh.com)

        :param adj: boolean adjacency matrix. If adj_j,i is True,
            then there is a link from i to j
        :type adj: scipy.sparse.csr.csr_matrix
        :param beta: 1-teleportation probability.
        :param epsilon: stop condition. Minimum allowed amount of
            change in the PagePops between iterations.
        :return: PagePop array normalized
        :rtype: ``numpy.ndarray``
        """
        beta = beta or self.beta
        epsilon = epsilon or self.epsilon

        n, _ = adj.shape
        # Test adjacency matrix is OK
        assert (adj.shape == (n, n))

        # Constants Speed-UP
        deg_out_beta = adj.sum(axis=0).T / beta  # vector

        # Initialize
        scores = np.ones((n, 1)) / n  # vector

        iterations = 0
        flag = True
        while flag:
            iterations += 1
            with np.errstate(divide='ignore'):
                # Ignore division by 0 on scores/deg_out_beta
                new_scores = adj.dot((scores / deg_out_beta))  # vector
            # Leaked PagePop
            new_scores += (1 - new_scores.sum()) / n
            # Stop condition
            if np.linalg.norm(scores - new_scores, ord=1) <= epsilon:
                flag = False
            scores = new_scores

        self.scores = scores
        return scores

    def save(self):
        """
        Associates each onion with its score, using the parallel
        structures: self.domain_idxs, self.scores, and stores the
        results in the DB: PagePop model
        """
        # Bulk Delete
        PagePopScore.objects.all().delete()

        # Associate onion with its score and create PagePop objs
        objs = []
        for onion, index in self.domains_idxs.items():
            kwargs = {
                'onion': onion,
                'score': self.scores[index],
            }
            new_obj = PagePopScore(**kwargs)
            objs.append(new_obj)

        # Bulk Save the objects into the DB
        PagePopScore.objects.bulk_create(objs)

        # save stats
        self._store_page_pop_stats()

    def build_pagescores(self, documents=None):
        """
        Calculate the popularity of each domain and save scores to
        `self.scores`, and the respecting indices in `self.domain_idxs`.

        :param documents: An iterable that yields all the ES documents.
            If not provided, the instance (class) attribute is used.
        """
        doc_generator = documents or self.documents

        adj_graph = self.build_adjacency_graph(doc_generator)
        matrix = self.build_sparse_matrix(adj_graph)
        _ = self.compute_page_pop(matrix)
