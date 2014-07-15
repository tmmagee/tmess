from django import template

register = template.Library()

@register.filter
def accounttype(value, arg=''):
  if value == 'm':
    return 'Member'
  elif value == 'o':
    return 'Organization'
  elif value == 'n':
    return 'Non-Member'
  else:
    return 'Unknown'
