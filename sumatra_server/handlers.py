from piston.handler import BaseHandler
from piston.utils import rc, validate
from sumatra.recordstore.django_store import models
import datetime
from django.core.urlresolvers import reverse
from django.db.models import ForeignKey
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from forms import PermissionsForm

"""
Note that in the Wikipedia REST article, the verb table differs slightly from
what is in the Piston documentation. In Wikipedia, it states that for an
element URI (e.g. a simulation record here), PUT should be used to create a
new element with a specified ID, while POST should be used to treat the resource
as a collection and add a subordinate. Piston says use POST to an element URI
to create a new resource. The Wikipedia approach seems more logical to me, so I'm
using it.
"""


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
    model = models.Record
    fields = ('label', 'timestamp', 'reason', 'outcome', 'duration',
              'executable', 'repository', 'main_file', 'version', 'diff',
              'dependencies', 'parameters', 'launch_mode', 'datastore',
              'output_data', 'platforms', 'tags', 'user', 'project_id',
              'script_arguments', 'input_datastore', 'input_data',
              'stdout_stderr')
    template = "record_detail.html"
    
    def queryset(self, request): # this is already defined in more recent versions of Piston
        return self.model.objects.all()
    
    @classmethod
    def project_id(self, record):
        return record.project.id
    
    @check_permissions
    def read(self, request, project, label):
        filter = {'project': project, 'label': label}
        try:
            return self.queryset(request).get(**filter)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
        
    @check_permissions
    def update(self, request, project, label):
        # this performs update if the record already exists, and create otherwise
        filter = {'project': project, 'label': label}
        attrs = self.flatten_dict(request.data)
        #print attrs
        try:
            # need to check consistency between URL project, group, timestamp
            # and the same information in request.data
            # we should also limit the fields that can be updated
            updatable_fields = ('reason', 'outcome', 'tags')
            inst = self.queryset(request).get(**filter)
            for field_name in updatable_fields:
                setattr(inst, field_name, attrs[field_name])
            inst.save()
            return rc.ALL_OK
        except self.model.DoesNotExist:
            # check consistency between URL project, label
            # and the same information in attrs. Remove those items from attrs
            assert label == attrs["label"]
            prj, created = models.Project.objects.get_or_create(id=filter["project"])
            if created:
                prj.projectpermission_set.create(user=request.user)
            inst = self.model(project=prj, label=label)
            fields = [field for field in self.model._meta.fields if field.name not in ('project', 'label', 'db_id')]
            for field in fields:
                if isinstance(field, ForeignKey):
                    fk_model = field.rel.to
                    obj_attrs = keys2str(attrs[field.name])
                    ##print field.name, fk_model, obj_attrs
                    fk_inst, created = fk_model.objects.get_or_create(**obj_attrs)
                    setattr(inst, field.name, fk_inst)
                else:
                    ##print field.name, attrs[field.name], type(attrs[field.name])
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
    def delete(self, request, project, label):
        filter = {'project': project, 'label': label}
        response = BaseHandler.delete(self, request, **filter)
        if response.status_code == 410: # Using 404 instead of 410 if resource doesn't exist
            response = rc.NOT_FOUND # to me 'Gone' implies it used to exist, and we can't say that for sure
        return response


class ProjectHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')
    template = "project_detail.html"
    
    def read(self, request, project):
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user=request.user)
        except models.Project.DoesNotExist:
            return rc.FORBIDDEN
        records = prj.record_set.all()
        tags = request.GET.get("tags", None)
        if tags:
            records = records.filter(tags__contains=tags)
        protocol = request.is_secure() and "https" or "http"
        project_uri = "%s://%s%s" % (protocol, request.get_host(), reverse("sumatra-project", args=[prj.id]))
        return {
                    'id': prj.id,
                    'name': prj.get_name(),
                    'description': prj.description,
                    'records': [ "%s%s/" % (project_uri, rec.label)
                                for rec in records],
                    'access': [perm.user.username for perm in prj.projectpermission_set.all()],
                    'tags': tags,
                }

    def update(self, request, project):
        """Create a new project and give the current user permission to access it."""
        if request.user.is_anonymous():
            return rc.FORBIDDEN
        prj, created = models.Project.objects.get_or_create(id=project)
        if created:
            prj.projectpermission_set.create(user=request.user)
            return rc.CREATED
        else:
            return rc.DUPLICATE_ENTRY


class PermissionListHandler(BaseHandler):
    allowed_methods = ('GET', 'POST',)
    template = "project_permissions.html"
    
    def read(self, request, project):
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user=request.user)
        except models.Project.DoesNotExist:
            return rc.FORBIDDEN
        return {
                    'id': prj.id,
                    'name': prj.get_name(),
                    'access': [perm.user for perm in prj.projectpermission_set.all()],
                }

    @validate(PermissionsForm)
    def create(self, request, project):
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user=request.user)
        except models.Project.DoesNotExist:
            return rc.FORBIDDEN
        prj.projectpermission_set.create(user=request.form.cleaned_data["user"])
        return HttpResponseRedirect(reverse("sumatra-project", args=[prj.id]))


class ProjectListHandler(BaseHandler):
    allowed_methods = ('GET',)
    template = "project_list.html"
    
    def read(self, request):
        if request.user.is_anonymous():
            user, _ = User.objects.get_or_create(username="anonymous")
            user.set_password("")
        else:
            user = request.user
        protocol = request.is_secure() and "https" or "http"
        return [ {
                    "id": prj.id,
                    "name": prj.get_name(),
                    "description": prj.description,
                    "uri": "%s://%s%s" % (protocol, request.get_host(), reverse("sumatra-project", args=[prj.id])),
                  }
                  for prj in models.Project.objects.filter(projectpermission__user=user) ]
        

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

class DataKeyHandler(BaseHandler):
    allowed_methods = []
    model = models.DataKey

# note: if we start to look at the Accept header, should send 406 response if we can't send the requested mimetype (RFC 2616)
