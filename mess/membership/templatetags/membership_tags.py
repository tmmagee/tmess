from django import template
from mess.membership import models

register = template.Library()

@register.filter
def work_status(value):
  """
  Returns a more descriptive work status
  """
  for status in models.WORK_STATUS:
    if status[0]==value:
      return status[1]

  return "WORK STATUS NOT FOUND"

@register.filter    
def member_status(value):
  """
  Returns a more descriptive member status
  """
  for status in models.MEMBER_STATUS:
    if status[0]==value:
      return status[1]

  return "MEMBER STATUS NOT FOUND"
