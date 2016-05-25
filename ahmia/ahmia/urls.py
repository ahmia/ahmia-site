"""The URL patterns of the ahmia."""
from django.conf import settings
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

# search app urls
urlpatterns = patterns('',
    url(r'^', include('search.urls')),
)

# robots.txt file
urlpatterns += patterns('',
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
    content_type='text/plain')),
)

# media files: CSS, JavaScript, images
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),
    )