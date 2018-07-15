from datetime import timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from ... import utils
from ...models import TorStats, I2PStats, SearchQuery, SearchResultsClick


class Command(BaseCommand):
    def __init__(self):
        super(Command, self).__init__()
        self.days_to_keep = settings.USAGE_STATS_DAYS

    def handle(self, *args, **options):
        self.cleanup_stats_etc()

    def cleanup_stats_etc(self):
        # *Stats tables
        oldest_day_to_keep = utils.timezone_today() - timedelta(days=self.days_to_keep)
        TorStats.objects.filter(day__lt=oldest_day_to_keep).delete()
        I2PStats.objects.filter(day__lt=oldest_day_to_keep).delete()

        # SearchQueries and Clicks
        oldest_datetime_to_keep = timezone.now() - timedelta(days=self.days_to_keep)
        SearchQuery.objects.filter(created__lt=oldest_datetime_to_keep).delete()
        SearchResultsClick.objects.filter(created__lt=oldest_datetime_to_keep).delete()
