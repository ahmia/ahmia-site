from django.contrib import admin

from .models import *


class PagePopAdmin(admin.ModelAdmin):
    ordering = ('-score',)


class PagePopStatsAdmin(admin.ModelAdmin):
    ordering = ('-day',)


class MetricAdmin(admin.ModelAdmin):
    ordering = ('-occurrences',)


class StatsAdmin(admin.ModelAdmin):
    ordering = ('-day',)


admin.site.register(HiddenWebsite)
admin.site.register(PagePopScore, PagePopAdmin)
admin.site.register(PagePopStats, PagePopStatsAdmin)
admin.site.register(SearchResultsClick, MetricAdmin)
admin.site.register(SearchQuery, MetricAdmin)
admin.site.register(TorStats, StatsAdmin)
admin.site.register(I2PStats, StatsAdmin)
