from piston.handler import BaseHandler
from piston.utils import rc
from sumatra.recordstore.django_store import models
import datetime
from django.core.urlresolvers import reverse
from django.db.models import ForeignKey
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

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
    timestamp = build_timestamp(**kwargs)
    filter = {'timestamp__gte': timestamp,
              'timestamp__lt': timestamp + one_second}
    filter['project'] = kwargs['project']
    filter['group'] = kwargs['group']
    return filter

def build_timestamp(**kwargs):
    D = {}
    for key in 'year', 'month', 'day', 'hour', 'minute', 'second':
        D[key] = int(kwargs[key])
    return datetime.datetime(**D)

def keys2str(D):
    """Keywords cannot be unicode."""
    E = {}
    for k,v in D.items():
        E[str(k)] = v
    return E


def check_permissions(func):
    def wrapper(self, request, project, *args, **kwargs):
        if request.user.projectpermission_set.filter(project__id=project).count():
            return func(self, request, project, *args, **kwargs)
        else:
            return rc.FORBIDDEN
    return wrapper


class RecordHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = models.SimulationRecord
    fields = ('group', 'timestamp', 'reason', 'outcome', 'duration',
              'executable', 'repository', 'main_file', 'version', 'diff',
              'dependencies', 'parameters', 'launch_mode', 'datastore',
              'data_key', 'platforms', 'tags', 'user')
    
    def queryset(self, request): # this is already defined in more recent versions of Piston
        return self.model.objects.all()
    
    @check_permissions
    def read(self, request, project, group, year, month, day, hour, minute, second):
        filter = build_filter(**locals())
        try:
            return self.queryset(request).get(**filter)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
    
    @check_permissions
    def update(self, request, project, group, year, month, day, hour, minute, second):
        # this performs update if the record already exists, and create otherwise
        filter = build_filter(**locals())
        attrs = self.flatten_dict(request.data)
        #print attrs
        try:
            # need to check consistency between URL project, group, timestamp
            # and the same information in request.data
            # we should also limit the fields that can be updated
            updatable_fields = ('reason', 'outcome') # tags
            inst = self.queryset(request).get(**filter)
            for field_name in updatable_fields:
                setattr(inst, field_name, attrs[field_name])
            inst.save()
            return rc.ALL_OK
        except self.model.DoesNotExist:
            # check consistency between URL project, group, timestamp
            # and the same information in attrs. Remove those items from attrs
            prj, created = models.Project.objects.get_or_create(id=filter["project"])
            if created:
                prj.projectpermission_set.create(user=request.user)
            timestamp = build_timestamp(**locals())
            inst = self.model(project=prj, group=group, timestamp=timestamp)
            inst.id = "%s_%s" % (group, timestamp.strftime("%Y%m%d-%H%M%S"))
            fields = [field for field in self.model._meta.fields if field.name not in ('project', 'group', 'timestamp', 'id', 'db_id', 'tags')] # tags excluded temporarily because it's complicated
            for field in fields:
                if isinstance(field, ForeignKey):
                    fk_model = field.rel.to
                    obj_attrs = keys2str(attrs[field.name])
                    print field.name, fk_model, obj_attrs
                    fk_inst, created = fk_model.objects.get_or_create(**obj_attrs)
                    setattr(inst, field.name, fk_inst)
                else:
                    print field.name, attrs[field.name], type(attrs[field.name])
                    setattr(inst, field.name, attrs[field.name])
            inst.save()
            for field in self.model._meta.many_to_many:
                for obj_attrs in attrs[field.name]:
                    getattr(inst, field.name).get_or_create(**keys2str(obj_attrs))
            inst.save()
            return rc.CREATED
        except self.model.MultipleObjectsReturned: # this should never happen
            return rc.DUPLICATE_ENTRY

    @check_permissions
    def delete(self, request, project, group, year, month, day, hour, minute, second):
        filter = build_filter(**locals())
        return BaseHandler.delete(self, request, **filter)



class ProjectHandler(BaseHandler):
    allowed_methods = ('GET',)
    
    
    def read(self, request, project):
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user=request.user)
        except models.Project.DoesNotExist:
            return rc.FORBIDDEN
        return {
                    'name': prj.name,
                    'description': prj.description,
                    'groups': [ "http://%s%s" % (request.get_host(),
                                                 reverse("sumatra-simulation-group", args=[project, g]))
                                for g in prj.groups()],
                    'access': [perm.user.username for perm in prj.projectpermission_set.all()]
                }


class ProjectListHandler(BaseHandler):
    allowed_methods = ('GET',)
    
    def read(self, request):
        return [ {
                    "name": prj.name,
                    "description": prj.description,
                    "uri": "http://%s%s" % (request.get_host(), reverse("sumatra-project", args=[prj.id])),
                 }
                for prj in models.Project.objects.filter(project_permission__user=request.user) ]


class GroupHandler(BaseHandler):
    allowed_methods = ('GET', 'DELETE')
    
    @check_permissions
    def read(self, request, project, group):
        # possibly we should do the following in two stages, first see if
        # the project exists (return rc.NOT_HERE if not), then check for
        # permissions (and return rc.FORBIDDEN)
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user=request.user)
        except models.Project.DoesNotExist:
            return rc.FORBIDDEN
        project_uri = "http://%s%s" % (request.get_host(), reverse("sumatra-project", args=[prj.id]))
        return {
                    "name": group,
                    "project": project_uri,
                    "records": [ "%s%s/%s" % (project_uri, group, rec.timestamp.strftime("%Y%m%d-%H%M%S"))
                                for rec in prj.simulationrecord_set.filter(group=group)],
               }
    
    @check_permissions
    def delete(self, request, project, group):
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user=request.user)
        except models.Project.DoesNotExist:
            return rc.FORBIDDEN
        records = models.SimulationRecord.objects.filter(project=prj,
                                                         group=group)
        n = records.count()
        for record in records:
            record.delete()
        return HttpResponse(str(n), content_type='text/plain', status=200) # can't return 204, because that can't contain a body, and we need to return the number of records deleted

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
