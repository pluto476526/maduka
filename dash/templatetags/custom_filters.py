# dash/templatetags.py

from django import template

register = template.Library()

@register.filter
def format_time(value):
    if value is None or 0:
        return '0m: 0s'

    minutes = value // 60
    seconds = int(value % 60)

    if minutes == 0:
        return f'0m: {seconds}s'
    return f'{minutes}m: {seconds}s'
