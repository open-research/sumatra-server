from django.conf.urls.defaults import *
from piston.resource import Resource
from sumatra_piston.handlers import RecordHandler, ProjectHandler, ProjectListHandler, GroupHandler

record_resource = Resource(RecordHandler)
group_resource = Resource(GroupHandler)
project_resource = Resource(ProjectHandler)

urlpatterns = patterns('',
    url(r'^$', Resource(ProjectListHandler)),
    url(r'^(?P<project>[^/]+)/$', project_resource, name="sumatra-project"),
    url(r'^(?P<project>[^/]+)/(?P<group>[^/]+)/$', group_resource, name="sumatra-simulation-group"),
    url(r'^(?P<project>[^/]+)/(?P<group>[^/]+)/(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})',
        record_resource, name="sumatra-simulation-record"),
)
