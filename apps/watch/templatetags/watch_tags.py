from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely retrieves a value from a dictionary trying original key, int(key), and str(key)."""
    if not isinstance(dictionary, dict):
        return None
    val = dictionary.get(key)
    if val is not None:
        return val
    try:
        val = dictionary.get(int(key))
        if val is not None:
            return val
    except (ValueError, TypeError):
        pass
    try:
        val = dictionary.get(str(key))
        if val is not None:
            return val
    except (ValueError, TypeError):
        pass
    return None
