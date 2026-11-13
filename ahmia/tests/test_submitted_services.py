import json
from urllib.request import urlopen

from django.test import LiveServerTestCase, override_settings


@override_settings(ALLOWED_HOSTS=['localhost', '127.0.0.1'])
class SubmittedServicesTests(LiveServerTestCase):
    def test_empty_submitted_services_can_be_requested_as_json(self):
        with urlopen(f'{self.live_server_url}/add/onionsadded/?format=json') as response:
            self.assertEqual(response.headers.get_content_type(), 'application/json')
            self.assertEqual(json.load(response), {'services': []})

    def test_json_lists_each_submitted_service_once_in_order(self):
        from ahmia.models import HiddenWebsite

        for url in [
            'http://zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz.onion/one',
            'http://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion/',
            'http://mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm.onion/',
            'http://bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.onion/',
            'http://zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz.onion/two',
        ]:
            HiddenWebsite.objects.create(onion=url)

        with urlopen(f'{self.live_server_url}/add/onionsadded/?format=json') as response:
            self.assertEqual(json.load(response), {'services': [
                'http://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion/',
                'http://bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.onion/',
                'http://mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm.onion/',
                'http://zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz.onion/',
            ]})

    def test_html_remains_the_default(self):
        from ahmia.models import HiddenWebsite

        HiddenWebsite.objects.create(
            onion='http://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion/path'
        )
        with urlopen(f'{self.live_server_url}/add/onionsadded/') as response:
            self.assertEqual(response.headers.get_content_type(), 'text/html')
            self.assertIn(
                b'http://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion/',
                response.read(),
            )
