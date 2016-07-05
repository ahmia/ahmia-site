"""Forms used in Ahmia."""
from django import forms
from django.core.exceptions import ObjectDoesNotExist

from .models import HiddenWebsite, HiddenWebsitePopularity

class AddOnionForm(forms.Form):
    """Request to add an onion domain."""
    onion = forms.CharField()

def add_result(answer, host, results):
    """Add new search result and get the stats about it."""
    if host:
        onion_id = host.replace(".onion", "")
        tor2web, backlinks, clicks = get_popularity(onion_id)
        if tor2web > 0 or backlinks > 0 or clicks > 0:
            results.append(Popularity(host, answer, tor2web, backlinks, clicks))
    else:
        results.append(Popularity(host, answer, 1, 1, 1))

def get_popularity(onion):
    """Calculate the popularity of an onion page."""
    try:
        hs = HiddenWebsite.objects.get(id=onion)
    except ObjectDoesNotExist:
        return 1, 1, 1
    if hs.banned:
        return 0, 0, 0
    try:
        pop = HiddenWebsitePopularity.objects.get(about=hs)
        clicks = pop.clicks
        public_backlinks = pop.public_backlinks
        tor2web = pop.tor2web
        return tor2web, public_backlinks, clicks
    except ObjectDoesNotExist:
        return 1, 1, 1

def sort_results(p_tuples):
    """Sort the results according to stats."""
    # Scaling the number of backlinks
    p_by_backlinks = sorted(p_tuples,
                            key=lambda popularity: popularity.backlinks,
                            reverse=True)
    for index, p_info in enumerate(p_by_backlinks):
        p_info.backlinks = 1 / (float(index) + 1)
    # Scaling the number of clicks
    p_by_clicks = sorted(p_by_backlinks,
                         key=lambda popularity: popularity.clicks,
                         reverse=True)
    for index, p_info in enumerate(p_by_clicks):
        p_info.clicks = 1 / (float(index) + 1)
    # Scaling the number of Tor2web
    p_by_tor2web = sorted(p_by_clicks,
                          key=lambda popularity: popularity.tor2web,
                          reverse=True)
    for index, p_info in enumerate(p_by_tor2web):
        p_info.tor2web = 1 / (float(index) + 1)
    p_by_sum = sorted(p_by_tor2web,
                      key=lambda popularity: popularity.sum(),
                      reverse=True)
    answer = []
    for p_info in p_by_sum:
        answer.append(p_info.content)
    return answer

class Popularity(object):
    """Popularity by Tor2web visits, backlinks and clicks."""
    def __init__(self, url, content, tor2web, backlinks, clicks):
        self.url = url
        self.content = content
        self.score = content.score
        self.tor2web = float(tor2web)
        self.backlinks = float(backlinks)
        self.clicks = float(clicks)
    def func(self):
        """Print the sum function."""
        print "1.5*%f * 1.5*%f * 1.0*%f + %f" % \
            self.tor2web, self.backlinks, self.clicks, self.score
    def sum(self):
        """Calculate the popularity."""
        #The model can be very simple (sum)
        #What are the proper coefficients?
        sum_function = 2.0*self.tor2web * 3.0*self.backlinks * 1.0*self.clicks \
                       + self.score
        print "\n"
        print "content.score =    " + str(self.score)
        print "sum_function  =    " + str(sum_function)
        print "\n"
        return sum_function
    def __repr__(self):
        return repr((self.url, self.tor2web,
                     self.backlinks, self.clicks, self.sum))
