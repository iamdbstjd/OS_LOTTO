from django import template


register = template.Library()


@register.filter
def ball_class(number):
    try:
        value = int(number)
    except (TypeError, ValueError):
        return "ball-neutral"

    if value <= 10:
        return "ball-yellow"
    if value <= 20:
        return "ball-blue"
    if value <= 30:
        return "ball-red"
    if value <= 40:
        return "ball-gray"
    return "ball-green"


@register.filter
def won(value):
    try:
        amount = int(value or 0)
    except (TypeError, ValueError):
        amount = 0
    return f"{amount:,}원"
