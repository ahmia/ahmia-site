from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, build_opener

from django.test import LiveServerTestCase, override_settings


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@override_settings(ALLOWED_HOSTS=['localhost', '127.0.0.1'])
class RedirectTests(LiveServerTestCase):
    def test_rejects_backslash_before_allowlisted_host(self):
        query = urlencode({
            'search_term': 'example',
            'redirect_url': 'https://evil.example\\@www.redirectionprogram.com/',
        })
        opener = build_opener(NoRedirect())
        with self.assertRaises(HTTPError) as response:
            opener.open(f'{self.live_server_url}/search/redirect?{query}')
        self.assertEqual(response.exception.code, 400)

    def test_rejects_malformed_destination(self):
        query = urlencode({
            'search_term': 'example',
            'redirect_url': 'https://[invalid/',
        })
        opener = build_opener(NoRedirect())
        with self.assertRaises(HTTPError) as response:
            opener.open(f'{self.live_server_url}/search/redirect?{query}')
        self.assertEqual(response.exception.code, 400)

    def test_redirects_to_allowlisted_help_site(self):
        destination = 'https://www.redirectionprogram.com/support'
        query = urlencode({'search_term': 'example', 'redirect_url': destination})
        with self.assertRaises(HTTPError) as response:
            build_opener(NoRedirect()).open(f'{self.live_server_url}/search/redirect?{query}')
        self.assertEqual(response.exception.code, 302)
        self.assertEqual(response.exception.headers['Location'], destination)

    def test_rejects_banned_onion(self):
        from ahmia.models import BannedWebsite

        domain = 'juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion'
        BannedWebsite.objects.create(onion=domain)
        query = urlencode({'search_term': 'example', 'redirect_url': f'http://{domain}/'})
        with self.assertRaises(HTTPError) as response:
            build_opener(NoRedirect()).open(f'{self.live_server_url}/search/redirect?{query}')
        self.assertEqual(response.exception.code, 400)

    def test_redirects_to_unbanned_onion(self):
        destination = 'http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/path'
        query = urlencode({'search_term': 'example', 'redirect_url': destination})
        with self.assertRaises(HTTPError) as response:
            build_opener(NoRedirect()).open(f'{self.live_server_url}/search/redirect?{query}')
        self.assertEqual(response.exception.code, 302)
        self.assertEqual(response.exception.headers['Location'], destination)
