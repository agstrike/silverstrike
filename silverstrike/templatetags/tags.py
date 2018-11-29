from django import template


register = template.Library()


@register.filter
def negate(value):
    return -value


@register.filter
def intvalue(value):
    return int(value)
