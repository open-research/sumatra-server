from piston.handler import BaseHandler
from sumatra.recordstore.django_store import models
import datetime
from django.core.urlresolvers import reverse

"""
Note that in the Wikipedia REST article, the verb table differs slightly from
what is in the Piston documentation. In Wikipedia, it states that for an
element URI (e.g. a simulation record here), PUT should be used to create a
new element with a specified ID, while POST should be used to treat the resource
as a collection and add a subordinate. Piston says use POST to an element URI
to create a new resource. The Wikipedia approach seems more logical to me, so I'm
using it.
"""

one_second = datetime.timedelta(0, 1)

def build_filter(**kwargs):
    D = {}
    for key in 'year', 'month', 'day', 'hour', 'minute', 'second':
        D[key] = int(kwargs[key])
    timestamp = datetime.datetime(**D)
    filter = {'timestamp__gte': timestamp,
              'timestamp__lt': timestamp + one_second}
    filter['project'] = kwargs['project']
    filter['group'] = kwargs['group']
    return filter


class RecordHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = models.SimulationRecord
    fields = ('group', 'timestamp', 'reason', 'outcome', 'duration',
              'executable', 'repository', 'main_file', 'version', 'diff',
              'dependencies', 'parameters', 'launch_mode', 'datastore',
              'data_key', 'platforms', 'tags')
    
    def queryset(self, request): # this is already defined in more recent versions of Piston
        return self.model.objects.all()
    
    def read(self, request, project, group, year, month, day, hour, minute, second):
        filter = build_filter(**locals())
        return self.queryset(request).get(**filter)
    
    def update(self, request, project, group, year, month, day, hour, minute, second):
        # this performs update if the record already exists, and create otherwise
        filter = build_filter(locals())
        attrs = self.flatten_dict(request.data)()
        try:
            # need to check consistency between URL project, group, timestamp
            # and the same information in request.data
            # we should also limit the fields that can be updated
            inst = self.queryset(request).get(**filter)
            for k,v in attrs.iteritems(): # not sure this handles foreign key fields
                setattr(inst, k, v)
            inst.save()
            return rc.ALL_OK
        except self.model.DoesNotExist:
            inst = self.model(**attrs) # not sure this handles foreign key fields
            inst.save()
            return rc.CREATED
        except self.model.MultipleObjectsReturned: # this should never happen
            return rc.DUPLICATE_ENTRY

    def delete(self, request, project, group, year, month, day, hour, minute, second):
        filter = build_filter(locals())
        return BaseHandler.delete(self, request, **filter)



class ProjectHandler(BaseHandler):
    allowed_methods = ('GET',)
    
    def read(self, request, project):
        prj = models.Project.objects.get(id=project)
        return {
                    'name': prj.name,
                    'description': prj.description,
                    'groups': [ "http://%s%s" % (request.get_host(),
                                                 reverse("sumatra-simulation-group", args=[project, g]))
                                for g in prj.groups()]
                }


class ProjectListHandler(BaseHandler):
    allowed_methods = ('GET',)
    
    def read(self, request):
        return [ {
                    "name": prj.name,
                    "description": prj.description,
                    "uri": "http://%s%s" % (request.get_host(), reverse("sumatra-project", args=[prj.id])),
                 }
                for prj in models.Project.objects.all() ]


class GroupHandler(BaseHandler):
    allowed_methods = ('GET',)
    
    def read(self, request, project, group):
        prj = models.Project.objects.get(id=project)
        project_uri = "http://%s%s" % (request.get_host(), reverse("sumatra-project", args=[prj.id]))
        return {
                    "name": group,
                    "project": project_uri,
                    "records": [ "%s%s/%s" % (project_uri, group, rec.timestamp.strftime("%Y%m%d-%H%M%S"))
                                for rec in prj.simulationrecord_set.filter(group=group)],
               }
                


# the following are currently defined only to suppress the 'id'
# in the output

class ExecutableHandler(BaseHandler):
    allowed_methods = []
    model = models.Executable
    
class ParameterSetHandler(BaseHandler):
    allowed_methods = []
    model = models.ParameterSet
    
class RepositoryHandler(BaseHandler):
    allowed_methods = []
    model = models.Repository
    
class LaunchModeHandler(BaseHandler):
    allowed_methods = []
    model = models.LaunchMode
    
class DatastoreHandler(BaseHandler):
    allowed_methods = []
    model = models.Datastore
    
class PlatformHandler(BaseHandler):
    allowed_methods = []
    model = models.PlatformInformation
    
class DependencyHandler(BaseHandler):
    allowed_methods = []
    model = models.Dependency