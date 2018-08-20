from django.contrib import admin

from .models import *


class PagePopAdmin(admin.ModelAdmin):
    ordering = ('-score',)


class MetricAdmin(admin.ModelAdmin):
    ordering = ('-occurrences',)


class SearchQueryAdmin(MetricAdmin):
    pass


class SearchResultsClickAdmin(MetricAdmin):
    pass


admin.site.register(HiddenWebsite)
admin.site.register(PagePopScore, PagePopAdmin)
admin.site.register(PagePopStats)
admin.site.register(SearchResultsClick, SearchResultsClickAdmin)
admin.site.register(SearchQuery, SearchQueryAdmin)
admin.site.register(TorStats)
admin.site.register(I2PStats)
