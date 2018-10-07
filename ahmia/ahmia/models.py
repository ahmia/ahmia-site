"""Models for the database of ahmia."""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import models, DatabaseError
from django.utils import timezone

from . import utils
from .validators import validate_onion_url, validate_status, validate_onion

logger = logging.getLogger("ahmia")


class HiddenWebsite(models.Model):
    """Hidden service website."""
    # For instance: http://3g2upl4pq6kufc4m.onion/
    onion = models.URLField(validators=[validate_onion_url, validate_status],
                            unique=True)

    def __str__(self):
        return str(self.onion)


class PagePopScoreManager(models.Manager):
    """
    Manager for PagePopScore Model
    """
    def get_or_None(self, **kwargs):
        """
        :param kwargs: same that would be given to get()
        :return: the object found or None
        """
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def get_score(self, **kwargs):
        """
        Returns the score but handles the DoesNotExist case
        returning None instead.

        :param kwargs: the lookup attributes for get()
        :rtype: float
        """
        try:
            return self.get(**kwargs).score
        except self.model.DoesNotExist:
            return None


class PagePopScore(models.Model):
    """
    Note: This will be called by bulk create thus
    save(), pre_save(), post_save() will not be called
    """
    onion = models.URLField(
        validators=[validate_onion, validate_status],
        unique=True)
    score = models.FloatField(
        default=0,
        verbose_name='PagePop score',
        help_text='Score as returned by PagePop algorithm')

    objects = PagePopScoreManager()

    def __str__(self):
        return "{0}: {1}".format(self.onion, self.score)


class PagePopStats(models.Model):
    """One entry/row is created by rank_pages command"""
    day = models.DateField(default=utils.timezone_today, unique=True)
    num_links = models.IntegerField(
        null=True,
        verbose_name='Number of Links',
        help_text='Number of links in general')
    num_edges = models.IntegerField(
        null=True,
        verbose_name='Number of Edges',
        help_text='Number of Unique inter-domain Links')
    num_nodes = models.IntegerField(
        null=True,
        verbose_name='Number of nodes',
        help_text='Number of onion domains (nodes)')

    def __str__(self):
        return str(self.day)


# *** Statistics related models and managers following *** #

class MetricQuerySet(models.QuerySet):
    """Custom queryset to be used to filter SearchQueries per time"""

    def today(self):
        """Used to count the daily number so far"""

        utc = timezone.now()
        today_start = utc.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.filter(updated__gte=today_start)

    def month(self):
        """
        Filter the queryset by looking up `settings.USAGE_STATS_DAYS`
        (default 30) back
        """

        utc = timezone.now()
        oldest_utc = utc - timedelta(days=settings.USAGE_STATS_DAYS)
        return self.filter(updated__gte=oldest_utc)


class MetricManager(models.Manager):
    def get_queryset(self):
        return MetricQuerySet(self.model, using=self._db)

    def today(self):
        return self.get_queryset().today()

    def month(self):
        return self.get_queryset().month()

    def add_or_increment(self, **kwargs):
        """
        Handles Metric table updates:
        If object does not exist create it, else update the
        counter (occurrences) of same instances in the table

        :param kwargs: A Dict containing the attributes that identify the obj
        :return the object that was created or updated
        """

        try:
            obj, created = self.get_or_create(**kwargs)
            if not created:
                obj.occurrences += 1
            obj.save()

        except DatabaseError as e:
            logger.exception(e)
            obj = None
            # stats shouldn't disrupt website functionality

        return obj


class Metric(models.Model):
    """Abstract base class for all Metric models"""
    NETWORKS = (
        ('T', 'TOR'),
        ('I', 'I2P'),
    )

    updated = models.DateTimeField(default=timezone.now)
    network = models.CharField(max_length=1, default='T', choices=NETWORKS)
    occurrences = models.IntegerField(default=1)

    objects = MetricManager()

    class Meta:
        abstract = True


class SearchQuery(Metric):
    """Used for search stastistics"""
    search_term = models.CharField(max_length=64)

    def __str__(self):
        return self.search_term[:25]

    class Meta:
        unique_together = ('search_term', 'network')


class SearchResultsClick(Metric):
    """Used for clicks statistics"""
    clicked = models.URLField()
    onion_domain = models.URLField(validators=[validate_onion_url])
    search_term = models.CharField(max_length=64)

    def __str__(self):
        return self.clicked[:50]

    class Meta:
        unique_together = ("clicked", "search_term", "onion_domain")


# todo Reconsider the current workflow: We recalculate Stats for
# the current day when `manage.py update_stats` is ran. Thus it
# ends up being redundant to keep *Stats tables in the DB?

class StatsQuerySet(models.QuerySet):
    """Custom queryset to be used to filter Stats per time"""

    def month(self):
        """
        Actually rather than looking into the current month (e.g April)
        we filter back `settings.USAGE_STATS_DAYS` (default 30) days
        """
        # todo can we merge with MetricManager.month - DRY ?

        utc = timezone.now().date()
        oldest_utc = utc - timedelta(days=settings.USAGE_STATS_DAYS)
        return self.filter(day__gte=oldest_utc)


class Stats(models.Model):
    """
    Abstract base class. Subclasses to be used for storing precalculated
    statistics, computed by update_stats management command (app: stats)
    """

    # horizontal axis: 30 last days (common for 4 plots)
    day = models.DateField(unique=True, default=utils.timezone_today)

    # Vertical axis: Metrics (4 plots)
    num_queries = models.IntegerField(default=0)
    num_unique_queries = models.IntegerField(default=0)
    num_clicks = models.IntegerField(default=0)
    num_unique_clicks = models.IntegerField(default=0)

    objects = StatsQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ['day']


class TorStats(Stats):
    def __str__(self):
        return str("Tor stats: %s" % self.day)


class I2PStats(Stats):
    def __str__(self):
        return str("I2P stats: %s" % self.day)
