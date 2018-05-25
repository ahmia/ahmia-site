# -*- coding: utf-8 -*-
"""Download data from Elasticsearch and convert it to Gexf/XML format."""
import networkx as nx  # Network modeling library
from elasticsearch import Elasticsearch  # Elasticsearch connection
from urlparse import urlparse
import time
from random import randint


def query(graph, es, color):
    """Make query and create a graph."""
    # Status of doc_type in the READ onion index
    index = "crawl"
    q = 'links.link:*'
    res = es.search(index=index, q=q)
    size = res['hits']['total']
    print "READ Index onions size in this range is %d" % size
    start = 0
    limit = 1
    # added = 0
    # updated = 0
    while start < size:
        time.sleep(1)
        try:
            res = es.search(index=index, from_=start, size=limit, q=q)
        except Exception as e:
            print e
            continue
        print "range=%d-%d, hits %d" % (start, start+limit, len(res['hits']['hits']))
        for hit in res['hits']['hits']:
            item = hit["_source"]
            graph.add_node(item["domain"])
            graph.node[item["domain"]]['viz'] = {
                'color': color,
                'position': {'x': randint(0, 100), 'y': randint(0, 100), 'z': randint(0, 100)}
            }
            for link in item["links"]:
                link = link["link"]
                if ".onion/" in link:
                    # print link
                    # parsed_uri = urlparse(link)
                    domain = link  # '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                    # graph.add_node(domain)
                    # graph.node[domain]['viz'] = {'color': color}
                    graph.add_edge(item["domain"], domain)
        start = start + limit


def use_data(es):
    """Use Elasticsearch data."""

    graph = nx.Graph()
    color = {'r': 0, 'g': 255, 'b': 0, 'a': 0.8}
    query(graph, es, color)
    print "The number of nodes %d" % len(graph.nodes())
    print "The number of edges %d" % len(graph.edges())
    nx.write_gexf(graph, "onionlinks.gexf", encoding='utf-8', prettyprint=True, version='1.2draft')


def main():
    """Main function."""
    es = Elasticsearch(timeout=60)
    use_data(es)


if __name__ == '__main__':
    main()
