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
            # Extract the description part after the colon
            if ':' in display:
                parts = display.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return display
    return value


@register.filter
def get_kp_display(value):
    """Get display name for Knowledge Profile"""
    from academics.models import KP_CHOICES
    for code, display in KP_CHOICES:
        if code == value:
            # Extract the description part after the colon
            if ':' in display:
                parts = display.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return display
    return value


@register.filter
def get_pa_display(value):
    """Get display name for Problem Attribute"""
    from academics.models import PA_CHOICES
    for code, display in PA_CHOICES:
        if code == value:
            # Extract the description part after the colon
            if ':' in display:
                parts = display.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return display
    return value


@register.filter
def get_a_display(value):
    """Get display name for Activity Attribute"""
    from academics.models import A_CHOICES
    for code, display in A_CHOICES:
        if code == value:
            # Extract the description part after the colon
            if ':' in display:
                parts = display.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return display
    return value


@register.filter
def add(value, arg):
    """Add arg to value"""
    try:
        return str(value) + str(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        arg_float = float(arg)
        if arg_float == 0:
            return 0
        return float(value) / arg_float
    except (ValueError, TypeError):
        return 0

