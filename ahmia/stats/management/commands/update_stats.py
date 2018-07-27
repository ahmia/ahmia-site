import datetime
import logging
import os

from django.conf import settings
from django.core import management
# from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand
from django.db import IntegrityError
from django.db.models import Sum

from ahmia import utils
from ahmia.models import SearchQuery, SearchResultsClick, I2PStats, TorStats
from ... import plots

logger = logging.getLogger("stats")


class Command(BaseCommand):
    help = 'Calculate the usage statistics for the past day and updates Stats tables'

    def __init__(self):
        super(Command, self).__init__()
        self.today = utils.timezone_today()

    def handle(self, *args, **options):
        tor_kwargs = self.calculate_stats(network='T')
        i2p_kwargs = self.calculate_stats(network='I')

        self.update_stats(TorStats, **tor_kwargs)
        self.update_stats(I2PStats, **i2p_kwargs)

        self.generate_plots()

        # collect the figures from ahmia/ahmia/static to ahmia/staticfiles
        management.call_command('collectstatic', interactive=False)

    @staticmethod
    def calculate_stats(network='T'):
        """
        Calculate traffic for the current day

        :param network: T for TOR or I for I2P
        :return: stats numbers as dict following model's attributes naming
        """

        # todo assuming that update_stats runs periodically and consistently
        # we currently recalculate only the last day in each run. Consider if
        # we should rather filter the whole month or settings.USAGE_STATS_DAYS

        past_day_queries = SearchQuery.objects.today().filter(network=network)
        past_day_clicks = SearchResultsClick.objects.today().filter(network=network)
        num_queries = past_day_queries.aggregate(Sum('occurrences'))['occurrences__sum']
        num_clicks = past_day_clicks.aggregate(Sum('occurrences'))['occurrences__sum']

        kwargs = {
            'num_queries': num_queries or 0,
            'num_clicks': num_clicks or 0,
            'num_unique_queries': len(past_day_queries) or 0,
            'num_unique_clicks': len(past_day_clicks) or 0
        }
        return kwargs

    def update_stats(self, modelclass, **kwargs):
        """
        Update modelclass table with current day traffic

        :param modelclass: A subclass of Stats (not instance)
        :param kwargs: the current day stats
        """

        try:
            obj = modelclass.objects.get(day=self.today)

        except modelclass.DoesNotExist:
            # if not exist add the unique field (day) and save the new obj
            kwargs['day'] = self.today
            try:
                modelclass.objects.create(**kwargs)
            except IntegrityError as e:
                logging.exception(e)

        else:
            # assuming kwargs returned by calculate_stats match the model's fields:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            try:
                obj.full_clean()
                obj.save()
            except (ValidationError, IntegrityError) as e:
                logging.exception(e)

        logger.info("Updated {0} for: {1} ".format(modelclass.__name__, self.today))

    @staticmethod
    def generate_plots():
        """
        Create plots for last month based on the data inside Stats subclasses
        """

        # stats_folder = staticfiles_storage.url('stats')
        # TODO find a better solution to this madness. the above didn't work
        stats_folder = settings.ROOT_PATH('ahmia', 'static', 'stats')

        tor_stats = TorStats.objects.month()
        i2p_stats = I2PStats.objects.month()

        # Days, x-axis, should be same, but better be carefull
        tor_days = tor_stats.values_list('day', flat=True)
        i2p_days = i2p_stats.values_list('day', flat=True)

        # horizontal common axis for all figures containing date strings
        tor_x = [datetime.datetime.strftime(d, "%d") for d in tor_days]
        i2p_x = [datetime.datetime.strftime(d, "%d") for d in i2p_days]

        # queries (TOR)
        y1 = list(tor_stats.values_list('num_queries', flat=True))
        y2 = list(tor_stats.values_list('num_unique_queries', flat=True))
        image_path = os.path.join(stats_folder, 'tor_queries.png')
        plots.generate_figure(tor_x, y1, y2, image_path, 'Search Queries')

        # clicks (TOR)
        y1 = list(tor_stats.values_list('num_clicks', flat=True))
        y2 = list(tor_stats.values_list('num_unique_clicks', flat=True))
        image_path = os.path.join(stats_folder, 'tor_clicks.png')
        plots.generate_figure(tor_x, y1, y2, image_path, 'Result Clicks')

        # queries (I2P)
        y1 = list(i2p_stats.values_list('num_queries', flat=True))
        y2 = list(i2p_stats.values_list('num_unique_queries', flat=True))
        image_path = os.path.join(stats_folder, 'i2p_queries.png')
        plots.generate_figure(i2p_x, y1, y2, image_path, 'Search Queries')

        # clicks (I2P)
        y1 = list(i2p_stats.values_list('num_clicks', flat=True))
        y2 = list(i2p_stats.values_list('num_unique_clicks', flat=True))
        image_path = os.path.join(stats_folder, 'i2p_clicks.png')
        plots.generate_figure(i2p_x, y1, y2, image_path, 'Result Clicks')
