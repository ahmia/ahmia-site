from django.core.management import BaseCommand


class UpdateStats(BaseCommand):
    help = 'Calculates usage statistics until this moment. Most probably invoked by cron'

    def handle(self, *args, **options):
        SearchQuery.object.all('')
