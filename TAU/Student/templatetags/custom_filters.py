from django import template
from django.utils import timezone
from django.template.defaultfilters import date as date_filter

register = template.Library()

@register.filter(name='ist_format')
def ist_format(value):
    """
    Format datetime in IST with timezone indicator
    Example output: "31 March 2024, 2:30 PM IST"
    """
    if value:
        # Ensure the datetime is timezone aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value)
        # Convert to IST
        ist_time = timezone.localtime(value)
        # Format the time
        return date_filter(ist_time, "d F Y, g:i A") + " IST"
    return "" 