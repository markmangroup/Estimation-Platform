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


@register.filter(name='get_proposal_id')
def get_proposal_id(proposal_ids, index):
    """ Returns the proposal ID at the given index """
    try:
        return proposal_ids[index]
    except IndexError:
        return None  # Return None if index is out of range