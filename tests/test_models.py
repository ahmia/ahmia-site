"""Tests: ahmia/tests/test_models.py is testing ahmia/models.py"""
import hashlib

from django.test import TestCase

from ahmia.models import (HiddenWebsite, HiddenWebsiteDescription,
                          HiddenWebsitePopularity)


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

class HiddenWebsiteDescriptionTest(TestCase):
    """Test HiddenWebsiteDescription model."""

    def setUp(self):
        """Creating models."""
        onions = HiddenWebsite.objects.all()
        self.assertEqual(HiddenWebsiteDescription.objects.all().count(), 4234)
        index = 0
        while index < 10:
            descr = HiddenWebsiteDescription.objects.create(about=onions[index])
            descr.title = "This is the title" + str(index)
            descr.description = "This is the description" + str(index)
            descr.relation = "http://example.com/" + str(index)
            descr.subject = "This, is, the, subject" + str(index)
            descr.type = "This is the type" + str(index)
            if index % 2 == 0:
                descr.officialInfo = True
            else:
                descr.officialInfo = False
            descr.full_clean()
            descr.save()
            index = index + 1
        self.assertEqual(HiddenWebsiteDescription.objects.all().count(), 4244)

    def test_description_works(self):
        """Test all the properties of the description."""
        index = 0
        onions = HiddenWebsite.objects.all()
        while index < 10:
            descr = HiddenWebsiteDescription.objects.get(about=onions[index],
            type="This is the type" + str(index))
            text = "This is the description" + str(index)
            self.assertEqual(descr.description, text)
            descr.description = ""
            if index % 2 == 0:
                self.assertTrue(descr.officialInfo)
            else:
                descr.officialInfo = True
            descr.save()
            # Get it again using filter and test that it has saved values
            descr = HiddenWebsiteDescription.objects.filter(about=onions[index])
            descr = descr.latest('updated')
            self.assertTrue(descr.officialInfo)
            self.assertEqual(descr.description, "")
            index = index + 1

    def delete_test(self):
        """Delete each object that was created in the init."""
        index = 0
        onions = HiddenWebsite.objects.all()
        while index < 10:
            descr = HiddenWebsiteDescription.objects.filter(about=onions[index])
            descr = descr.latest('updated').delete()
            descr = HiddenWebsiteDescription.objects.filter(about=onions[index])
            descr = descr.latest('updated').delete()
        self.assertEqual(HiddenWebsiteDescription.objects.all().count(), 4234)

class HiddenWebsitePopularityTest(TestCase):
    """Test HiddenWebsitePopularity model."""

    def setUp(self):
        """Creating models."""
        onions = HiddenWebsite.objects.all()
        self.assertEqual(HiddenWebsitePopularity.objects.all().count(), 1391)
        index = 0
        while index < 10:
            pop = HiddenWebsitePopularity.objects.filter(about=onions[index])
            pop = pop[0]
            pop.tor2web = 0
            if index % 2 == 0:
                pop.clicks = 10
            elif index % 3 == 0:
                pop.public_backlinks = 100
            pop.full_clean()
            pop.save()
            index = index + 1
        self.assertEqual(HiddenWebsitePopularity.objects.all().count(), 1391)

    def test_popularity_works(self):
        """Test all the properties of the popularity."""
        index = 0
        onions = HiddenWebsite.objects.all()
        while index < 10:
            pop = HiddenWebsitePopularity.objects.get(about=onions[index])
            self.assertEqual(pop.tor2web, 0)
            pop.tor2web = 1000
            if index % 2 == 0:
                self.assertEqual(pop.clicks, 10)
            elif index % 3 == 0:
                self.assertEqual(pop.public_backlinks, 100)
            pop.save()
            index = index + 1
        # Get it again using filter and test that it has saved values
        pops = HiddenWebsitePopularity.objects.filter(tor2web=1000)
        self.assertEqual(pops.count(), 10)
        self.assertEqual(pops[3].clicks, 10)
