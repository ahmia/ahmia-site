import itertools
import logging

import numpy as np
from scipy import sparse

from ahmia import utils
from ahmia.models import PagePopScore, PagePopStats
from ahmia.validators import is_valid_full_onion_url, is_valid_onion

logger = logging.getLogger('ahmia')


def is_legit_link(link, entry):
    """
    Estimate whether a link is legit or not (check: hidden links, etc)

    TODO: ignore hidden links, links to mirror sites (efficiently..)
          or any other tricky / promoting links
    """
    if link['link_name']:
        return True
    return False


class PagePopHandler(object):

    def __init__(self, entries=None, domains=None, beta=0.85, epsilon=10 ** -6):
        """
        Handler for PagePop algorithm. It uses a :dict: `domain_idxs` in
        order to assign each domain an id, that's the corresponding
        index to `scores`, list, that hold the pagepop scores.
        ``self.num_domains`` is used as  a counter while building
        adjacency matrix and ``domain_idxs`` is also stored as an
        instance attribute for statistics purposes.

        todo: profile code to reduce execution time (critical for local pagepop)
        todo: simplify by merging domain_idxs and scores?

        :param entries: An iterable to fetch entries from. It should be a
            generator in order to reduce memory used.
        :param domains: If non-empty then inspect only the links that point
            to webpages under these domains
        :param beta: 1-teleportation probability.
        :param epsilon: stop condition. Minimum allowed amount of change
            in the PagePops between iterations.
        """
        self.entries = entries
        self.domains = domains
        self.beta = beta
        self.epsilon = epsilon

        self.domains_idxs = {}
        self.scores = None

        self.num_domains = 0
        self.num_links = None
        self.num_edges = None

    def get_scores_as_dict(self):
        """
        Associate onion with its score and returns the corresponding dict

        :rtype dict
        """
        objs = {}
        for onion, index in self.domains_idxs.items():
            objs[onion] = float(self.scores[index])

        return objs

    def get_scores(self):
        """
        Associate onion with its score and returns PagePopScore objs

        :rtype list
        """
        objs = []
        for onion, index in self.domains_idxs.items():
            kwargs = {
                'onion': onion,
                'score': self.scores[index],
            }
            new_obj = PagePopScore(**kwargs)
            objs.append(new_obj)

        return objs

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

    def save(self):
        """
        Associates each onion with its score, using the parallel
        structures: self.domain_idxs, self.scores, and stores the
        results in the DB: PagePop model
        """
        # Bulk Delete
        PagePopScore.objects.all().delete()

        # Associate onion with its score and create PagePopScore objs
        objs = self.get_scores()

        # Bulk Save the objects into the DB
        PagePopScore.objects.bulk_create(objs)

        # save stats
        self._store_page_pop_stats()

    def build_pagescores(self, entries=None, domains=None):
        """
        Calculate the popularity of each domain and save scores to
        `self.scores`, and the respecting indices in `self.domain_idxs`.

        :param entries: An iterable that yields all the ES entries.
            If not provided, the instance (class) attribute is used.
        :param domains: If non-empty then inspect only the links that point
            to webpages under these domains
        """
        es_entries = entries or self.entries
        domains = domains or self.domains

        adj_graph = self._build_adjacency_graph(es_entries, domains)
        matrix = self._build_sparse_matrix(adj_graph)
        _ = self._compute_page_pop(matrix)

    def _build_adjacency_graph(self, entries, domains):
        """
        Constructs adjacency graph for outgoing links, saves to self.adj_graph

        todo: mv ES entries/documents parsing in separate function

        :param entries: An iterable that contains the ES entries.
            Preferably a generator to reduce RAM usage.
        :param domains: If non-empty then inspect only the links that point
            to webpages under these domains
        :return: adjacency matrix
        :rtype: ``list`` of tuples
        """
        entries = entries or self.entries
        adj_graph = []

        for e in entries:
            if '_source' in e:
                # if called by `calc_page_pop.py` then `e` is an ES document
                e = e['_source']

            if 'domain' in e:
                # entry from crawled page
                origin = e['domain']
            elif 'source' in e:
                # entry from anchor text
                origin = e['source']
            else:
                logger.warning('rank_pages: Unable to process: %s' % e)
                continue

            origin = utils.extract_domain_from_url(origin)
            if is_valid_onion(origin):
                origin_idx = self._get_domain_idx(origin)

                links = e.get('links', [])  # crawled case
                if 'target' in e:  # anchor case
                    links.append({'link': e['target']})

                for l in links:
                    # ignore any links without text
                    if is_legit_link(l, e):
                        url = l['link']
                        if is_valid_full_onion_url(url):
                            destiny = utils.extract_domain_from_url(url)
                            # if domains non-empty ignore any other origins
                            if not domains or destiny in domains:
                                if destiny != origin:
                                    destiny_idx = self._get_domain_idx(destiny)
                                    adj_graph.append((origin_idx, destiny_idx))

        self.num_links = len(adj_graph)  # total links
        adj_graph = set(adj_graph)  # count only 1 edge of source->destiny
        self.num_edges = len(adj_graph)  # unique links

        return adj_graph

    def _build_sparse_matrix(self, adj_graph, num_nodes=None):
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

    def _compute_page_pop(self, adj, beta=None, epsilon=None):
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
