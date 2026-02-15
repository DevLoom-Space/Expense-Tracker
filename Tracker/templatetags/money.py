from django import template
register = template.Library()

@register.filter
def kes(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return value
    return f"KES {n:,.2f}"
