"""Tests: ahmia/tests/test_models.py is testing ahmia/models.py"""
from django.test import TestCase
import hashlib
from ahmia.models import HiddenWebsite

class HiddenWebsiteTest(TestCase):
    """Test HiddenWebsite model."""

    def setUp(self):
        """Creating models."""
        self.assertEqual(HiddenWebsite.objects.all().count(), 1410)
        chars = map(chr, range(97, 123))
        for index, char in enumerate(chars):
            url = "http://"+char*16+".onion/"
            id_str = url[7:-7]
            md5 = hashlib.md5(url[7:-1]).hexdigest()
            onion = HiddenWebsite.objects.create(id=id_str, url=url, md5=md5)
            if index % 2 == 0:
                onion.online = True
            if index % 3 == 0:
                onion.banned = True
            onion.save()
        # There should be 26 new instances
        self.assertEqual(HiddenWebsite.objects.all().count(), 1436)

    def test_hiddenwebsites_works(self):
        """Test all the properties of the hidden website."""
        self.assertEqual(HiddenWebsite.objects.all().count(), 1436)
        chars = map(chr, range(97, 123))
        # Test each model that was created.
        for index, char in enumerate(chars):
            onion = HiddenWebsite.objects.get(id=char*16)
            if index % 2 == 0:
                self.assertTrue(onion.online)
            if index % 3 == 0:
                self.assertTrue(onion.banned)
            # Test MD5sum
            md5 = hashlib.md5(onion.url[7:-1]).hexdigest()
            self.assertEqual(onion.md5, md5)
            # Modify
            onion.online = True
            onion.save() # Save
            # Get object again and test
            onion = HiddenWebsite.objects.get(id=char*16)
            self.assertTrue(onion.online)
        # Test filtering
        onion_id = "aaaaaaaaaaaaaaaa"
        onion = HiddenWebsite.objects.filter(id=onion_id)
        self.assertEqual(onion[0].id, onion_id)

    def delete_test(self):
        """Delete each object that was created in the init."""
        chars = map(chr, range(97, 123))
        for char in chars:
            onion = HiddenWebsite.objects.get(id=char*16)
            onion.delete()
