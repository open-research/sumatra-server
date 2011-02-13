from django import template
#from django.template.defaultfilters import stringfilter
#from django.utils.safestring import mark_safe
from sumatra_server.forms import PermissionsForm

register = template.Library()

@register.simple_tag
def insert_permission_form():
    return PermissionsForm()["user"]