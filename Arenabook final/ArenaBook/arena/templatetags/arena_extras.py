"""Small template helpers used across the ArenaBook templates."""
from django import template

register = template.Library()


@register.filter
def money(value):
    """Format a decimal as Indian rupees with thousands separators."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    return f"{value:,.2f}"


@register.filter
def attr(field, attributes):
    """Usage: {{ form.field|attr:"placeholder:Your name,rows:4" }}"""
    for pair in attributes.split(","):
        if ":" in pair:
            key, val = pair.split(":", 1)
            field.field.widget.attrs[key.strip()] = val.strip()
    return field


@register.filter
def times(number):
    try:
        return range(int(number))
    except (TypeError, ValueError):
        return range(0)


@register.filter
def percent_of(value, total):
    try:
        total = float(total)
        if total == 0:
            return 0
        return round(float(value) / total * 100, 1)
    except (TypeError, ValueError):
        return 0


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Rebuild the current querystring with some keys replaced (pagination)."""
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()


@register.filter
def pretty(value):
    """credit_card -> Credit Card"""
    return str(value).replace("_", " ").title()
