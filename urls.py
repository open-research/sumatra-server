from django.conf.urls.defaults import *
from piston.authentication import HttpBasicAuthentication
from sumatra_piston.handlers import RecordHandler, ProjectHandler, ProjectListHandler#, GroupHandler
from sumatra_piston.resource import Resource

auth = HttpBasicAuthentication(realm='Sumatra Server API')
   
record_resource = Resource(RecordHandler, authentication=auth)
project_resource = Resource(ProjectHandler, authentication=auth)

urlpatterns = patterns('',
    url(r'^$', Resource(ProjectListHandler), name="sumatra-project-list"),
    url(r'^(?P<project>[^/]+)/$', project_resource, name="sumatra-project"),
    url(r'^(?P<project>[^/]+)/(?P<label>\w+[\w|\-\.]*)/$', record_resource, name="sumatra-record"),
)
