"""Tags used in ahmia's templates"""
from django import template
from django.conf import settings

register = template.Library()

@register.assignment_tag
def is_development_environment():
    """Test if template is rendered in debug mode"""
    return settings.DEBUG


@register.simple_tag
def get_environment():
    """Return environment mode"""
    if settings.DEBUG:
        return 'development'
    else:
        return 'production'
