from django.core.exceptions import ValidationError
from django.test import TestCase

from ..validators import validate_full_onion_url, validate_onion_url, validate_onion


class UrlValidatorsTestCase(TestCase):

    def call_validator(self, validator, valid_urls, invalid_urls):
        """
        Helper handler for test fuctions, since validators are
        called/handled commonly
        :param validator: A reference to model validator function
        :param valid_urls: An iterable with valid inputs
        :param invalid_urls: An iterable with invalid inputs
        :return: None
        :raises: failureException
        """
        for vu in valid_urls:
            try:
                validator(vu)
            except ValidationError:
                self.fail("%s was mistakenly found invalid" % vu)

        for invu in invalid_urls:
            with self.assertRaises(ValidationError):
                validator(invu)

    def test_validate_full_onion_url(self):
        valid_urls = [
            "http://msydqstlz2kzerdg.onion/search/?q=tor+network&d=7",
            "http://beta-1.msydqstlz2kzerdg.onion/search/?q=tor",
            "https://2alpha.msydqstlz2kzerdgaaaa222222222222222222223333333333444444.onion",
        ]
        invalid_urls = [
            "http://msydqstlz2kzerdg1.onion",  # domain length 17
            "http//msydqstlz2kzerdg1.onion",   # typo in protocol
            "http://msydqstlz2kzerdg.onionnonono",
            "msydqstlz2kzerdg.onion",  # protocol missing
            "http://msydqstlz2kzerdg1.aonion",   # wrong TLD
            "http://9sydqstlz2kzerdg1.onion",  # contains '9'
            "http://msydqstlz2-zerdg1.onion/node",  # contains '-'
            "http://msydqstlz2kzerdg1.onion.onion",  # onion: invalid domain
        ]
        self.call_validator(validate_full_onion_url, valid_urls, invalid_urls)

    def test_validate_onion_url(self):
        valid_urls = [
            "http://msydqstlz2kzerdg.onion/",
            "http://beta-1.msydqstlz2kzerdg.onion/",
            "https://2alpha.msydqstlz2kzerdgaaaa222222222222222222223333333333444444.onion",
        ]
        invalid_urls = [
            "http://msydqstlz2kzerdg1.onion",  # domain length 17
            "http://msydqstlz2kzerdg.onionnonono",
            "msydqstlz2kzerdg.onion",  # protocol missing
            "http://msydqstlz2kzerdg1.aonion",
            "http://9sydqstlz2kzerdg1.onion",  # contains '9'
            "http://msydqstlz2-zerdg1.onion",  # contains '-'
            "http://msydqstlz2azerdg1.onion.onion",  # onion: invalid domain
            "http://msydqstlz2kzerdg.onion/search",  # contains path
        ]
        self.call_validator(validate_onion_url, valid_urls, invalid_urls)

    def test_validate_onion(self):
        valid_urls = [
            "msydqstlz2kzerdg.onion",
            "msydqstlz2kzerdg",
            "msydqstlz2kzerdgaaaa222222222222222222223333333333444444"
        ]
        invalid_urls = [
            "msydqstlz2kzerdg1.onion",  # domain length 17
            "http://msydqstlz2kzerdg.onion"  # contains protocol
            "msydqstlz2kzerdg.onion.onion",  # onion: invalid domain
            "9sydqstlz2kzerdg1.onion",  # contains '9'
            "msydqstlz2-zerdg1.onion",  # contains '-'
            "sydqstlz2kzerdg.onion/search",  # contains path
        ]
        self.call_validator(validate_onion, valid_urls, invalid_urls)
