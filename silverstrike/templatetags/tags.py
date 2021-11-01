from django import template


register = template.Library()


@register.filter
def negate(value):
    return -value


@register.filter
def intvalue(value):
    return int(value)


@register.filter
def dateformat_py2js(value):
    # https://bootstrap-datepicker.readthedocs.io/en/latest/options.html#format
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

    format_map = (
        ('dd', r'%d'),
        ('D', r'%a'),
        ('DD', r'%A'),
        ('mm', r'%m'),
        ('M', r'%b'),
        ('MM', r'%B'),
        ('yy', r'%y'),
        ('yyyy', r'%Y'),
    )

    for js_format, py_format in format_map:
        value = value.replace(py_format, js_format)
    return value

