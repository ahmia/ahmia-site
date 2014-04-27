"""Sort the search results from the back-end."""
# -*- coding: utf-8 -*-
from random import randint

class Popularity(object):
    """Popularity to URL by YaCy results, backlinks and clicks."""
    def __init__(self, url, yacy, backlinks, clicks):
        self.url = url
        self.yacy = float(yacy)
        self.backlinks = float(backlinks)
        self.clicks = float(clicks)
    def func(self):
        """Print the sum function."""
        print "3.0*%f + 2.0*%f + 1.0*%f" % self.yacy, self.backlinks, self.clicks
    def sum(self):
        """Calculate the popularity."""
        #The model can be very simple (sum)
        #What are the proper coefficients?
        sum_function = 3.0*self.yacy + 2.0*self.backlinks + 1.0*self.clicks
        return sum_function
    def __repr__(self):
        return repr((self.url, self.yacy, self.backlinks, self.clicks, self.sum))

def click_popularity(url):
    """How many times this URL has been clicked."""
    # Code database connection here
    return randint(1, 1000)

def backlink_popularity(url):
    """How many backlinks point to this URL."""
    # Code database connection here
    return randint(1, 1000)

def sort_results(results):
    """Sort the results again."""
    p_tuples = []
    for index, url in enumerate(results):
        backlinks = backlink_popularity(url)
        clicks = click_popularity(url)
        yacy = 1 / (float(index) + 1) #scale
        p_tuples.append(Popularity(url, yacy, backlinks, clicks))
    #Scaling the number of backlinks
    p_by_backlinks = sorted(p_tuples, key=lambda popularity: popularity.backlinks, reverse=True)
    for index, p_info in enumerate(p_by_backlinks):
        p_info.backlinks = 1 / (float(index) + 1)
    #Scaling the number of clicks
    p_by_clicks = sorted(p_by_backlinks, key=lambda popularity: popularity.clicks, reverse=True)
    for index, p_info in enumerate(p_by_clicks):
        p_info.clicks = 1 / (float(index) + 1)
    p_by_sum = sorted(p_by_clicks, key=lambda popularity: popularity.sum(), reverse=True)
    for p_info in p_by_sum:
        print p_info.url
        print "--- Popularity by YaCy (y):      %f" % p_info.yacy
        print "--- Popularity by backlinks (b): %f" % p_info.backlinks
        print "--- Popularity by clicks (c):    %f" % p_info.clicks
        print "--- Total: 3*y + 2*b + 1*c =     %f \n" % p_info.sum()

def main():
    """Main function."""
    #Generate example data
    #Example ordered results to a query from the YaCy back-end
    chars = map(chr, range(97, 123))
    yacy_results = []
    for char in chars:
        yacy_results.append("http://"+char*16+".onion/")
    sort_results(yacy_results)

if __name__ == '__main__':
    main()
    