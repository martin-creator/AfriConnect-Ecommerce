from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(str(key))
    return None  # or handle as you see fit


@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except TypeError:
        return 0  # Return 0 if there is a type error

