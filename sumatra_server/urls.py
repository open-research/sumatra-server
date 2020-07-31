"""
Sumatra Server

:copyright: Copyright 2010-2015 Andrew Davison
:license: BSD 2-clause, see COPYING for details.
"""

from django.conf.urls import url
from sumatra_server.views import (
    RecordResource,
    ProjectResource,
    ProjectListResource,
    PermissionListResource,
)

urlpatterns = [
    url(r"^$", ProjectListResource.as_view(), name="sumatra-project-list"),
    url(r"^(?P<project>[^/]+)/$", ProjectResource.as_view(), name="sumatra-project"),
    url(
        r"^(?P<project>[^/]+)/permissions/$",
        PermissionListResource.as_view(),
        name="sumatra-project-permissions",
    ),
    url(
        r"^(?P<project>[^/]+)/(?P<label>\w+[\w|\-\.]*)/$",
        RecordResource.as_view(),
        name="sumatra-record",
    ),
]
