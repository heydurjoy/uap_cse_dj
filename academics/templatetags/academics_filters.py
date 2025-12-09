from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def split_string(value, delimiter=','):
    """Split a string by delimiter"""
    if value is None:
        return []
    return value.split(delimiter)


@register.filter
def get_blooms_display(value):
    """Get display name for Bloom's level"""
    from academics.models import BLOOMS_CHOICES
    for code, display in BLOOMS_CHOICES:
        if code == value:
            return display.split(':')[1].strip() if ':' in display else display
    return value


@register.filter
def get_kp_display(value):
    """Get display name for Knowledge Profile"""
    from academics.models import KP_CHOICES
    for code, display in KP_CHOICES:
        if code == value:
            return display.split(':')[1].strip() if ':' in display else display
    return value


@register.filter
def get_pa_display(value):
    """Get display name for Problem Attribute"""
    from academics.models import PA_CHOICES
    for code, display in PA_CHOICES:
        if code == value:
            return display.split(':')[1].strip() if ':' in display else display
    return value


@register.filter
def get_a_display(value):
    """Get display name for Activity Attribute"""
    from academics.models import A_CHOICES
    for code, display in A_CHOICES:
        if code == value:
            return display.split(':')[1].strip() if ':' in display else display
    return value


@register.filter
def add(value, arg):
    """Add arg to value"""
    try:
        return str(value) + str(arg)
    except (ValueError, TypeError):
        return ''

