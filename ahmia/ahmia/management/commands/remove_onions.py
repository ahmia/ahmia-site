from django.core.management import BaseCommand

from ...models import HiddenWebsite


class Command(BaseCommand):
    help = 'Removes all the onion addresses stored in Elasticsearch'

    def handle(self, *args, **options):
        for address in HiddenWebsite.objects.all():
            address.delete()
