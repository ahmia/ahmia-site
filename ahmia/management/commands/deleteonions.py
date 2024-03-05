""" Delete all added onions """
from django.core.management.base import BaseCommand
from ahmia.models import HiddenWebsite

class Command(BaseCommand):
    """ Deletes all HiddenWebsite entries """
    help = 'Deletes all HiddenWebsite entries'

    def handle(self, *args, **kwargs):
        HiddenWebsite.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all HiddenWebsite entries'))
