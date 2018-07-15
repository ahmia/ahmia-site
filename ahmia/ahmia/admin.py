from django.contrib import admin


from .models import *

admin.site.register(HiddenWebsite)
admin.site.register(SearchResultsClick)
admin.site.register(SearchQuery)
admin.site.register(TorStats)
admin.site.register(I2PStats)
