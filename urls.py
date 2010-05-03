from django.conf.urls.defaults import *
from piston.resource import Resource
from sumatra_server.handlers import RecordHandler #, GroupHandler, ProjectHandler

record_resource = Resource(RecordHandler)
#group_resource = Resource(GroupHandler)
#project_resource = Resource(ProjectHandler)

urlpatterns = patterns('',
   url(r'^(?P<project>[^/]+)/(?P<group>[^/]+)/(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})', record_resource),
)


    