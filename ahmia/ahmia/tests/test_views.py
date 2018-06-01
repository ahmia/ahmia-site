"""Tests: ahmia/tests/test_views.py is testing ahmia/views.py"""
# -*- coding: utf-8 -*-
import codecs  # UTF-8 support for the text files
import os

from django.conf import settings
from django.test import TestCase
from django.utils.translation import ugettext as _


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
        # resp_content = resp.content.decode('utf-8')
        self.assertEqual(resp.status_code, 200)

        # todo: the following is currently disabled since it takes AGES to complete
        # compare with the expected html response which is in ./example_addresses.html
        # file_name = "{}/example_addresses.html".format(os.path.dirname(__file__))
        # raw_html = read_file(file_name)
        # self.assertHTMLEqual(raw_html, resp_content)

    def test_description_edition(self):
        """Edit a description and test the result."""

        # todo How does this work? Anyway we have to edit the disc before checking the result
        # resp = self.client.get('/address/')
        # hs_1 = resp.context['description_list'][0]
        #
        # self.assertEqual(resp.status_code, 200)
        # self.assertTrue('description_list' in resp.context)
        # self.assertEqual(hs_1.title, "Tor Bazaar Member's Forum")
        # self.assertTrue('count_banned' in resp.context)
        # self.assertEqual(resp.context['count_banned'], 13)
        # self.assertTrue('count_online' in resp.context)
        # self.assertEqual(resp.context['count_online'], 1331)

    def test_unknown(self):
        """Test locations that should answer 404 not found."""

        # Ensure that non-existent valid onion address throw a 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa')
        self.assertEqual(resp.status_code, 404)

        # todo disabled because no url rule matches and response varies on DEBUG value
        # resp_content = resp.content.decode('utf-8')
        # correct_result = "There is no aaaaaaaaaaaaaaaa.onion indexed."
        # self.assertEqual(resp_content, correct_result)

        # Ensure that the edition throws 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa/edit')
        self.assertEqual(resp.status_code, 404)

        # Ensure that the status throws 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa/status')
        self.assertEqual(resp.status_code, 404)

        # Ensure that the popularity throws 404
        resp = self.client.get('/address/aaaaaaaaaaaaaaaa/popularity')
        self.assertEqual(resp.status_code, 404)

    def test_invalid(self):
        """Test locations that should answer 400 bad request."""
        # todo currently no such url rule exists

        # resp = self.client.get('/address/invalid')
        # resp_content = resp.content.decode('utf-8')
        # correct_result = "Invalid onion domain: invalid"
        # self.assertEqual(resp.status_code, 400)
        # self.assertEqual(resp_content, correct_result)

    def test_add_onion(self):
        """ Test the add onion page (url: /add)"""

        a_valid_onion = _("http://msydqstlz2kzerdg.onion/")
        an_invalid_onion = _("http://length17nameaaaaa.onion/")
        successful_text = _("Your request to add a service was successfully submitted")
        failure_text = _("Your request to add a service was either invalid or already")

        # add a valid onion
        resp = self.client.post('/add/', {'onion': a_valid_onion})
        self.assertContains(resp, successful_text, status_code=200)

        # adding again the same onion should fail
        resp = self.client.post('/add/', {'onion': a_valid_onion})
        self.assertContains(resp, failure_text)

        # adding an invalid onion will also fail with the same message
        resp = self.client.post('/add/', {'onion': an_invalid_onion})
        self.assertContains(resp, failure_text)
