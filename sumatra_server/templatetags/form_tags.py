"""
Sumatra Server

:copyright: Copyright 2010-2015 Andrew Davison
:license: CeCILL, see COPYING for details.
"""

from django import template
from sumatra_server.forms import PermissionsForm

register = template.Library()


@register.simple_tag
def insert_permission_form():
    return PermissionsForm()["user"]
