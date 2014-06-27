"""Tests: ahmia/tests/test_views.py is testing ahmia/views.py"""
# -*- coding: utf-8 -*-
import codecs  # UTF-8 support for the text files
import os
import sys

from django.test import TestCase


def read_file(filename):
    """Read a file and return the text content."""
    inputfile = codecs.open(filename, "r", "utf-8")
    data = inputfile.read()
    inputfile.close()
    return data

class OnionAddressViewsTestCase(TestCase):
    """Test /address/ view."""
    def test_address_index_html(self):
        """Test to render the whole HTML page and compare it to the example."""
        resp = self.client.get('/address/')
        self.assertEqual(resp.status_code, 200)
        encoding = sys.getfilesystemencoding()
        this_path = os.path.dirname(unicode(__file__, encoding))
        file_name = this_path + "/example_addresses.html"
        raw_html = read_file(file_name)
        self.assertHTMLEqual(raw_html, resp.content)

    def test_description_edition(self):
        """Edit a description and test the result."""
        # Test the result
        resp = self.client.get('/address/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('description_list' in resp.context)
        hs_1 = resp.context['description_list'][0]
        self.assertEqual(hs_1.title, u"Tor Bazaar Member's Forum")
        self.assertTrue('count_banned' in resp.context)
        self.assertEqual(resp.context['count_banned'], 13)
        self.assertTrue('count_online' in resp.context)
        self.assertEqual(resp.context['count_online'], 1331)

    def test_unknown(self):
        """Test locations that should answer 404 not found."""
        # Ensure that non-existent valid onion address throw a 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa')
        self.assertEqual(resp.status_code, 404)
        correct_result = "There is no aaaaaaaaaaaaaaaa.onion indexed."
        self.assertEqual(resp.content, correct_result)
        # Ensure that the edition throws 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa/edit')
        self.assertEqual(resp.status_code, 404)
        correct_result = "There is no aaaaaaaaaaaaaaaa.onion indexed."
        self.assertEqual(resp.content, correct_result)
        # Ensure that the status throws 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa/status')
        self.assertEqual(resp.status_code, 404)
        # Ensure that the popularity throws 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa/popularity')
        self.assertEqual(resp.status_code, 404)

    def test_invalid(self):
        """Test locations that should answer 400 bad request."""
        resp = self.client.get('/address/invalid')
        self.assertEqual(resp.status_code, 400)
        correct_result = "Invalid onion domain: invalid"
        self.assertEqual(resp.content, correct_result)
