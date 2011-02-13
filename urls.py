from django.conf.urls.defaults import *
from piston.authentication import HttpBasicAuthentication
from sumatra_server.authentication import DjangoAuthentication, AuthenticationDispatcher
from sumatra_server.handlers import RecordHandler, ProjectHandler, ProjectListHandler, PermissionListHandler
from sumatra_server.resource import Resource

auth = AuthenticationDispatcher({'html': DjangoAuthentication()},
                                default=HttpBasicAuthentication(realm='Sumatra Server API'))

record_resource = Resource(RecordHandler, authentication=auth)
project_resource = Resource(ProjectHandler, authentication=auth)
permissionlist_resource = Resource(PermissionListHandler, authentication=auth)
print "AUTH:", project_resource.authentication

urlpatterns = patterns('',
    url(r'^$', Resource(ProjectListHandler), name="sumatra-project-list"),
    url(r'^(?P<project>[^/]+)/$', project_resource, name="sumatra-project"),
    url(r'^(?P<project>[^/]+)/permissions/$', permissionlist_resource, name="sumatra-project-permissions"),
    url(r'^(?P<project>[^/]+)/(?P<label>\w+[\w|\-\.]*)/$', record_resource, name="sumatra-record"),
)
