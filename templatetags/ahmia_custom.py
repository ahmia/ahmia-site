from django import template
from django.conf import settings

register = template.Library()

@register.assignment_tag
def is_development_environment():
    return settings.DEBUG == True

@register.simple_tag
def get_environment():
    if settings.DEBUG == True:
        return 'development'
    else:
        return 'production'
