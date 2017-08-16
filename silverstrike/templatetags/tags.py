from django import template


register = template.Library()


@register.filter
def negate(value):
    return -value
