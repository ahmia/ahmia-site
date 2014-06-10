"""Tests: ahmia/tests/test_views.py is testing ahmia/views.py"""
from django.test import TestCase
import codecs # UTF-8 support for the text files
import os, sys

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
