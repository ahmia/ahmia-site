from django.test import TestCase

from ahmia.lib.pagepop import PagePopHandler


class TestPagePop(TestCase):
    def test_compute_page_pop(self):
        p = PagePopHandler()

        # Case 1:
        # Consider 0,1,2,3 are A,B,C,D
        adj_mat = [
            (1, 0),  # B -> A
            (3, 0),  # D -> A
            (0, 2),  # A -> C
            (3, 1),  # D -> B
        ]

        sparse = p.build_sparse_matrix(adj_mat)
        ranks = p.compute_page_pop(sparse)
        # print(ranks)
        assert ranks[2] > ranks[0] > ranks[1] > ranks[3]  # C > A > B > D

        # Case 2:
        # Consider 0,1,2,3,4 are A,B,C,D,E
        adj_mat = [
            (0, 1),  # A -> B
            (1, 2),  # B -> C
            (2, 3),  # C -> D
            (3, 0),  # D -> A
            (4, 0),  # E -> A
        ]

        sparse = p.build_sparse_matrix(adj_mat)
        ranks = p.compute_page_pop(sparse, beta=0.6)
        # print(ranks)
        assert ranks[0] > ranks[1] > ranks[2] > ranks[3] > ranks[4]
