from django.contrib import admin

from .models import HiddenWebsite, SearchResultsClicks


admin.site.register(HiddenWebsite)
admin.site.register(SearchResultsClicks)
