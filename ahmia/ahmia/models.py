"""Models for the database of ahmia."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, IntegrityError
from django.utils import timezone

from . import utils
from .validators import validate_onion_url, validate_status

logger = logging.getLogger("ahmia")


class HiddenWebsite(models.Model):
    """Hidden service website."""
    # For instance: http://3g2upl4pq6kufc4m.onion/
    onion = models.URLField(validators=[validate_onion_url, validate_status], unique=True)

    def __str__(self):
        return str(self.onion)


# *** Stats related models and managers following *** #

class MetricQuerySet(models.QuerySet):
    """Custom queryset to be used to filter SearchQueries per time"""

    def today(self):
        """Used to count the daily number so far"""

        utc = timezone.now()
        today_start = utc.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.filter(created__gte=today_start)

    def month(self):
        """
        This follows different logic than today, since we lookup
        back `settings.USAGE_STATS_DAYS` (default 30) days instead
        of looking into the current month (e.g April)
        """

        utc = timezone.now()
        oldest_utc = utc - timedelta(days=settings.USAGE_STATS_DAYS)
        return self.filter(created__gte=oldest_utc)


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
            try:
                obj = self.get(**kwargs)
            except ObjectDoesNotExist:
                obj = self.create(**kwargs)
            else:
                obj.occurrences += 1
                obj.save()

        # todo find all possible Exceptions here
        except (IntegrityError, ValidationError, ValueError) as e:
            logger.exception(e)
            obj = None
            # pass, so that stats errors don't disrupt website functionality

        return obj


class Metric(models.Model):
    """Abstract base class for all Metric models"""
    NETWORKS = (
        ('T', 'TOR'),
        ('I', 'I2P'),
    )

    created = models.DateTimeField(default=timezone.now)
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


# todo The way the whole workflow ended up... it may be redundant
# to store Stats in database, since we are generating the plots
# each time we run update_stats. Consider again whats optimal

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
    """Abstract base class. Subclasses to be used for storing precalculated
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
