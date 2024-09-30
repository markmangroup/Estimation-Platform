from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def multiply(value, arg):
    """Multiplies the given value by the arg."""
    try:
        return value * arg
    except (TypeError, ValueError):
        return ""


@register.filter
def round_value(value, decimals=2):
    """Rounds the given value to the specified number of decimal places."""
    try:
        return round(float(value), int(decimals))
    except (TypeError, ValueError):
        return ""
