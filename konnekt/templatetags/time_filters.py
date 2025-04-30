from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def natural_time_format(value):
    now = timezone.now()
    delta = now - value

    if delta < timedelta(minutes=1):
        return "Just now"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} min ago"
    elif delta < timedelta(hours=24):
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hr ago"
    elif delta < timedelta(days=2):
        return "Yesterday"
    elif delta < timedelta(days=7):
        return f"{delta.days} days ago"
    else:
        return value.strftime("%b %d, %Y")

