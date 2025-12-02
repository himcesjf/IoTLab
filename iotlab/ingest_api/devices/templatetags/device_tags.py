from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    try:
        if total > 0:
            return (value / total) * 100
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0 