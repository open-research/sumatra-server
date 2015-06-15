"""
Sumatra Server

:copyright: Copyright 2010-2015 Andrew Davison
:license: CeCILL, see COPYING for details.
"""

from django.conf.urls import patterns, url
from sumatra_server.views import (RecordResource, ProjectResource,
                                  ProjectListResource, PermissionListResource)

urlpatterns = patterns('',
    url(r'^$',
        ProjectListResource.as_view(),
        name="sumatra-project-list"),
    url(r'^(?P<project>[^/]+)/$',
        ProjectResource.as_view(),
        name="sumatra-project"),
    url(r'^(?P<project>[^/]+)/permissions/$',
        PermissionListResource.as_view(),
        name="sumatra-project-permissions"),
    url(r'^(?P<project>[^/]+)/(?P<label>\w+[\w|\-\.]*)/$',
        RecordResource.as_view(),
        name="sumatra-record"),
)
