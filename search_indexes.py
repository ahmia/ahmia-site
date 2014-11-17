from ahmia.models import WebsiteIndex
from haystack import indexes


class Website(indexes.SearchIndex, indexes.Indexable):

    domain = indexes.CharField(model_attr='domain')
    url = indexes.CharField(model_attr='url')
    tor2web_url = indexes.CharField(model_attr='tor2web_url')
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    h1 = indexes.CharField(model_attr='h1')
    h2 = indexes.CharField(model_attr='h2')
    crawling_session = indexes.CharField(model_attr='crawling_session')
    server_header = indexes.CharField(model_attr='server_header')
    date_inserted = indexes.DateTimeField(model_attr='date_inserted')
    content_auto = indexes.EdgeNgramField(model_attr='content')

    def get_model(self):
        return WebsiteIndex
