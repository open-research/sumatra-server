"""
Sumatra Server

:copyright: Copyright 2010-2014 Andrew Davison
:license: CeCILL, see COPYING for details.
"""

from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc, validate
from sumatra.recordstore.django_store import models
import datetime
import logging
from django.core.urlresolvers import reverse
from django.db.models import ForeignKey
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from forms import PermissionsForm
from tagging.utils import parse_tag_input

"""
Note that in the Wikipedia REST article, the verb table differs slightly from
what is in the Piston documentation. In Wikipedia, it states that for an
element URI (e.g. a simulation record here), PUT should be used to create a
new element with a specified ID, while POST should be used to treat the resource
as a collection and add a subordinate. Piston says use POST to an element URI
to create a new resource. The Wikipedia approach seems more logical to me, so I'm
using it.
"""

logger = logging.getLogger("sumatra_server")


def build_timestamp(**kwargs):
    D = {}
    for key in 'year', 'month', 'day', 'hour', 'minute', 'second':
        D[key] = int(kwargs[key])
    return datetime.datetime(**D)


def keys2str(D):
    """Keywords cannot be unicode."""
    E = {}
    for k, v in D.items():
        E[str(k)] = v
    return E


def check_permissions(func):
    def wrapper(self, request, project, *args, **kwargs):
        if models.Project.objects.filter(id=project, projectpermission__user__username='anonymous').count():
            return func(self, request, project, *args, **kwargs)
        elif request.user.projectpermission_set.filter(project__id=project).count():
            return func(self, request, project, *args, **kwargs)
        else:
            return rc.FORBIDDEN
    return wrapper


class AnonymousRecordHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)
    model = models.Record
    fields = ('label', 'timestamp', 'reason', 'outcome', 'duration',
              'executable', 'repository', 'main_file', 'version', 'diff',
              'dependencies', 'parameters', 'launch_mode', 'datastore',
              'output_data', 'platforms', 'tags', 'user', 'project_id',
              'script_arguments', 'input_datastore', 'input_data',
              'stdout_stderr', 'repeats')
    template = "record_detail.html"

    @staticmethod
    def tags(obj):
        return parse_tag_input(obj.tags)

    @classmethod
    def project_id(self, record):
        return record.project.id

    def read(self, request, project, label):
        if not models.Project.objects.filter(id=project, projectpermission__user__username='anonymous').count():
            return rc.FORBIDDEN
        filter = {'project': project, 'label': label}
        try:
            return self.queryset(request).get(**filter)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class RecordHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = models.Record
    fields = ('label', 'timestamp', 'reason', 'outcome', 'duration',
              'executable', 'repository', 'main_file', 'version', 'diff',
              'dependencies', 'parameters', 'launch_mode', 'datastore',
              'output_data', 'platforms', 'tags', 'user', 'project_id',
              'script_arguments', 'input_datastore', 'input_data',
              'stdout_stderr', 'repeats')
    template = "record_detail.html"
    anonymous = AnonymousRecordHandler

    @staticmethod
    def tags(obj):
        return parse_tag_input(obj.tags)

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
        logger.debug("PUT -->", request.PUT)
        logger.debug("Data -->", request.data)
        attrs = self.flatten_dict(request.data)
        try:
            # need to check consistency between URL project, group, timestamp
            # and the same information in request.data
            # we should also limit the fields that can be updated
            updatable_fields = ('reason', 'outcome')
            inst = self.queryset(request).get(**filter)
            for field_name in updatable_fields:
                setattr(inst, field_name, attrs[field_name])
            #import pdb; pdb.set_trace()
            inst.tags = ",".join(attrs['tags'])
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
            fields = [field for field in self.model._meta.fields if field.name not in ('project', 'label', 'db_id', 'tags')]
            for field in fields:
                if isinstance(field, ForeignKey):
                    fk_model = field.rel.to
                    obj_attrs = keys2str(attrs[field.name])
                    fk_inst, created = fk_model.objects.get_or_create(**obj_attrs)
                    setattr(inst, field.name, fk_inst)
                else:
                    ##print field.name, attrs[field.name], type(attrs[field.name])
                    setattr(inst, field.name, attrs[field.name])
            inst.tags = ",".join(attrs['tags'])
            inst.save()
            for field in self.model._meta.many_to_many:
                for obj_attrs in attrs[field.name]:
                    getattr(inst, field.name).get_or_create(**keys2str(obj_attrs))
            inst.save()
            return rc.CREATED
        except self.model.MultipleObjectsReturned:  # this should never happen
            return rc.DUPLICATE_ENTRY

    @check_permissions
    def delete(self, request, project, label):
        filter = {'project': project, 'label': label}
        response = BaseHandler.delete(self, request, **filter)
        if response.status_code == 410:  # Using 404 instead of 410 if resource doesn't exist
            response = rc.NOT_FOUND      # to me 'Gone' implies it used to exist, and we can't say that for sure
        return response


class AnonymousProjectHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)
    template = "project_detail.html"

    def read(self, request, project):
        try:
            prj = models.Project.objects.get(id=project)
        except models.Project.DoesNotExist:
            return rc.NOT_FOUND
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user__username='anonymous')
        except models.Project.DoesNotExist:
            resp = HttpResponse("Authorization Required", content_type='text/plain', status=401)
            resp['WWW-Authenticate'] = 'Basic realm="%s"' % "Sumatra Server API"
            return resp
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
            'records': ["%s%s/" % (project_uri, rec.label)
                        for rec in records],
            'tags': tags,
        }


class ProjectHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')
    template = "project_detail.html"
    anonymous = AnonymousProjectHandler

    def read(self, request, project):
        anonymous, _ = User.objects.get_or_create(username="anonymous")
        try:
            prj = models.Project.objects.get(id=project, projectpermission__user__in=(request.user, anonymous))
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
            'records': ["%s%s/" % (project_uri, rec.label)
                        for rec in records],
            'access': [perm.user.username for perm in prj.projectpermission_set.all()],
            'tags': tags,
        }

    def update(self, request, project):
        """
        Create a new project and give the current user permission to access it,
        or update the name and description of an existing project.
        """
        if request.user.is_anonymous():
            return rc.FORBIDDEN
        prj, created = models.Project.objects.get_or_create(id=project)
        changed = False
        for attr in ("name", "description"):
            if attr in request.data:
                setattr(prj, attr, request.data[attr])
                changed = True
        if changed:
            prj.save()
        if created:
            prj.projectpermission_set.create(user=request.user)
            return rc.CREATED
        else:
            return rc.ALL_OK


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


class AnonymousProjectListHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)
    template = "project_list.html"

    def read(self, request):
        protocol = request.is_secure() and "https" or "http"
        return [
            {
                "id": prj.id,
                "name": prj.get_name(),
                "description": prj.description,
                "uri": "%s://%s%s" % (protocol, request.get_host(), reverse("sumatra-project", args=[prj.id])),
                "last_updated": prj.last_updated()
            }
            for prj in reversed(sorted(models.Project.objects.filter(projectpermission__user__username="anonymous"),
                                       key=lambda prj: prj.last_updated()))]


class ProjectListHandler(BaseHandler):
    allowed_methods = ('GET',)
    template = "project_list.html"
    anonymous = AnonymousProjectListHandler

    def read(self, request):
        anonymous, _ = User.objects.get_or_create(username="anonymous")
        protocol = request.is_secure() and "https" or "http"
        return [
            {
                "id": prj.id,
                "name": prj.get_name(),
                "description": prj.description,
                "uri": "%s://%s%s" % (protocol, request.get_host(), reverse("sumatra-project", args=[prj.id])),
                "last_updated": prj.last_updated()
            }
            for prj in reversed(sorted(models.Project.objects.filter(projectpermission__user__in=(request.user, anonymous)),
                                       key=lambda prj: prj.last_updated()))]


class AnonymousExecutableHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.Executable
    fields = ('name', 'options', 'path', 'version')


class ExecutableHandler(BaseHandler):
    allowed_methods = []
    model = models.Executable
    fields = ('name', 'options', 'path', 'version')
    anonymous = AnonymousExecutableHandler


class AnonymousParameterSetHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.ParameterSet


class ParameterSetHandler(BaseHandler):
    allowed_methods = []
    model = models.ParameterSet
    anonymous = AnonymousParameterSetHandler


class AnonymousRepositoryHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.Repository
    field = ('type', 'url', 'upstream')


class RepositoryHandler(BaseHandler):
    allowed_methods = []
    model = models.Repository
    field = ('type', 'url', 'upstream')
    anonymous = AnonymousRepositoryHandler


class AnonymousLaunchModeHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.LaunchMode
    fields = ('type', 'parameters')

    @staticmethod
    def parameters(obj):
        if obj.parameters:
            value = eval(obj.parameters, {'__builtins__': []}, {})
            assert isinstance(value, dict)
        else:
            value = {}
        return value


class LaunchModeHandler(BaseHandler):
    allowed_methods = []
    model = models.LaunchMode
    fields = ('type', 'parameters')
    anonymous = AnonymousLaunchModeHandler

    @staticmethod
    def parameters(obj):
        if obj.parameters:
            value = eval(obj.parameters, {'__builtins__': []}, {})
            assert isinstance(value, dict)
        else:
            value = {}
        return value


class AnonymousDatastoreHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.Datastore
    fields = ('type', 'parameters')

    @staticmethod
    def parameters(obj):
        if obj.parameters:
            value = eval(obj.parameters, {'__builtins__': []}, {})
            assert isinstance(value, dict)
        else:
            value = {}
        return value


class DatastoreHandler(BaseHandler):
    allowed_methods = []
    model = models.Datastore
    fields = ('type', 'parameters')
    anonymous = AnonymousDatastoreHandler

    @staticmethod
    def parameters(obj):
        if obj.parameters:
            value = eval(obj.parameters, {'__builtins__': []}, {})
            assert isinstance(value, dict)
        else:
            value = {}
        return value


class AnonymousPlatformHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.PlatformInformation
    fields = ('architecture_bits', 'architecture_linkage', 'ip_addr', 'machine', 'network_name',
              'processor', 'release', 'system_name', 'version')


class PlatformHandler(BaseHandler):
    allowed_methods = []
    model = models.PlatformInformation
    fields = ('architecture_bits', 'architecture_linkage', 'ip_addr', 'machine', 'network_name',
              'processor', 'release', 'system_name', 'version')
    anonymous = AnonymousPlatformHandler


class AnonymousDependencyHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.Dependency


class DependencyHandler(BaseHandler):
    allowed_methods = []
    model = models.Dependency
    anonymous = AnonymousDependencyHandler


class AnonymousDataKeyHandler(AnonymousBaseHandler):
    allowed_methods = []
    model = models.DataKey
    fields = ('path', 'digest', 'metadata')

    @staticmethod
    def metadata(obj):
        if obj.metadata:
            value = eval(obj.metadata, {'__builtins__': []}, {})
            assert isinstance(value, dict)
        else:
            value = {}
        return value


class DataKeyHandler(BaseHandler):
    allowed_methods = []
    model = models.DataKey
    fields = ('path', 'digest', 'metadata')
    anonymous = AnonymousDataKeyHandler

    @staticmethod
    def metadata(obj):
        if obj.metadata:
            value = eval(obj.metadata, {'__builtins__': []}, {})
            assert isinstance(value, dict)
        else:
            value = {}
        return value


# note: if we start to look at the Accept header, should send 406 response
# if we can't send the requested mimetype (RFC 2616)
