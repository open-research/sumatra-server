"""
Sumatra Server

:copyright: Copyright 2010-2015 Andrew Davison
:license: CeCILL, see COPYING for details.
"""


import json
from django.http import (HttpResponse, JsonResponse,
                         HttpResponseBadRequest,     # 400
                         HttpResponseForbidden,      # 403
                         HttpResponseNotFound,       # 404
                         HttpResponseNotAllowed,     # 405
                         HttpResponseNotModified,    # 304
                         HttpResponseRedirect)       # 302
from django.views.generic import View
from django.db.models import ForeignKey
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

from sumatra.recordstore.django_store.models import Project, Record
from serializers import (RecordSerializer, ProjectSerializer, ProjectListSerializer,
                         PermissionListSerializer)
from authentication import AuthenticationDispatcher
from forms import PermissionsForm


class HttpResponseNotAcceptable(HttpResponse):
    status_code = 406


media_type_abbreviations = {
    'html': 'text/html',
    'json': 'application/json',
    'record-v3+json': 'application/vnd.sumatra.record-v3+json',
    'project-v3+json': 'application/vnd.sumatra.project-v3+json',
    'project-list-v3+json': 'application/vnd.sumatra.project-list-v3+json',
    'record-v4+json': 'application/vnd.sumatra.record-v4+json',
    'project-v4+json': 'application/vnd.sumatra.project-v4+json',
    'project-list-v4+json': 'application/vnd.sumatra.project-list-v4+json'
}


def keys2str(D):
    """Keywords cannot be unicode."""  # unnecessary for Python 3?
    E = {}
    for k, v in D.items():
        E[str(k)] = v
    return E


def flatten_dict(dct):
    return dict([ (str(k), dct.get(k)) for k in dct.keys() ])


def check_permissions(func):
    def wrapper(self, request, *args, **kwargs):
        # if the resource is public (accessible to anonymous), continue
        try:
            project = Project.objects.get(id=kwargs['project'])
        except Project.DoesNotExist:
            return HttpResponseNotFound()
        auth = AuthenticationDispatcher()
        authenticated = auth.is_authenticated(request)
        if not request.user.username:
            request.user.username = 'anonymous'
        if project.projectpermission_set.filter(user__username='anonymous').count() == 0:
            # if the user is not authenticated, redirect to authentication
            if not authenticated:
                return auth.challenge()
            # check if the user is authorized
            if request.user.projectpermission_set.filter(project__id=kwargs["project"]).count() == 0:
                return HttpResponseForbidden()
        return func(self, request, *args, **kwargs)
    return wrapper


class ResourceView(View):
    """
    View subclass which determines the best media type to send.
    """

    def get_accepted_media_types(self, request):
        if "format" in request.GET:
            # 'format' in the URL over-rides the Accept header
            abbrev = request.GET['format']
            accepted_media_types = [media_type_abbreviations[abbrev]]
        else:
            # get mimetype from Accept header
            if 'HTTP_ACCEPT' in request.META:
                accept = request.META['HTTP_ACCEPT']
            elif 'Accept' in request.META:
                accept = request.META['Accept']
            else:
                accept = ""
            accepted_media_types = []
            if accept:
                qualities = []
                for mtwq in accept.split(","):
                    q = "q=1"
                    if ";" in mtwq:
                        mt, q = mtwq.split(";")  # this assumes only "q" parameter is present, not others such as "level"
                    accepted_media_types.append(mtwq.strip())
                    qualities.append(float(q.split("=")[1]))
                accepted_media_types = [mt for q, mt in sorted(zip(qualities, accepted_media_types))]
        return accepted_media_types

    def determine_media_type(self, request):
        # todo: handle partial wildcards in accepted media types
        accepted_media_types = self.get_accepted_media_types(request)
        if accepted_media_types:
            possible_media_types = [self.preferred_media_type, 'application/json', 'text/html']
            for mt in accepted_media_types:
                if mt in possible_media_types:
                    return mt
            if "*/*" in accepted_media_types:
                return self.preferred_media_type
            else:
                return None
        else:
            # RFC 2616 Section 14: If no Accept header field is present, then it is assumed that the client accepts all media types.
            return self.preferred_media_type


class RecordResource(ResourceView):
    preferred_media_type = 'application/vnd.sumatra.record-v4+json'
    serializer = RecordSerializer

    @check_permissions
    def get(self, request, *args, **kwargs):
        filter = {'project': kwargs['project'], 'label': kwargs['label']}
        try:
             record = Record.objects.get(**filter)
        except Record.DoesNotExist:
            return HttpResponseNotFound()

        media_type = self.determine_media_type(request)
        if media_type is None:
            return HttpResponseNotAcceptable()
        content = self.serializer(media_type).encode(record, kwargs['project'], request)
        return HttpResponse(content, content_type="{}; charset=utf-8".format(media_type), status=200)

    @csrf_exempt
    @check_permissions
    def put(self, request, *args, **kwargs):
        # this performs update if the record already exists, and create otherwise
        filter = {'project': kwargs["project"], 'label': kwargs["label"]}
        attrs = json.loads(request.body)
        try:
            # need to check consistency between URL project, group, timestamp
            # and the same information in request.data
            # we should also limit the fields that can be updated
            updatable_fields = ('reason', 'outcome')
            inst = Record.objects.get(**filter)
            for field_name in updatable_fields:
                setattr(inst, field_name, attrs[field_name])
            inst.tags = ",".join(attrs['tags'])
            inst.save()
            return HttpResponse('', status=200)
        except Record.DoesNotExist:
            # check consistency between URL project, label
            # and the same information in attrs. Remove those items from attrs
            assert kwargs["label"] == attrs["label"]
            project, created = Project.objects.get_or_create(id=filter["project"])
            if created:
                project.projectpermission_set.create(user=request.user)
            inst = Record(project=project, label=kwargs["label"])
            fields = [field for field in Record._meta.fields
                      if field.name not in ('project', 'label', 'db_id', 'tags')]
            for field in fields:
                if isinstance(field, ForeignKey):
                    fk_model = field.rel.to
                    obj_attrs = keys2str(attrs[field.name])
                    fk_inst, created = fk_model.objects.get_or_create(**obj_attrs)
                    setattr(inst, field.name, fk_inst)
                else:
                    setattr(inst, field.name, attrs[field.name])
            inst.tags = ",".join(attrs['tags'])
            inst.save()
            for field in Record._meta.many_to_many:
                for obj_attrs in attrs[field.name]:
                    getattr(inst, field.name).get_or_create(**keys2str(obj_attrs))
            for obj_attrs in attrs['output_data']:
                inst.output_data.get_or_create(**keys2str(obj_attrs))
            inst.save()
            return HttpResponse('Created', status=201)
        except Record.MultipleObjectsReturned:  # this should never happen
            return HttpResponse('Conflict/Duplicate', status=409)

    @check_permissions
    def delete(self, request, *args, **kwargs):
        filter = {'project': kwargs["project"], 'label': kwargs["label"]}
        try:
            record = Record.objects.get(**filter)
            record.delete()
            return HttpResponse('', status=204)
        except Record.MultipleObjectsReturned:
            return HttpResponse('Conflict/Duplicate', status=409)
        except Record.DoesNotExist:
            return HttpResponseNotFound()


class ProjectResource(ResourceView):
    preferred_media_type = 'application/vnd.sumatra.project-v4+json'
    serializer = ProjectSerializer

    @check_permissions
    def get(self, request, *args, **kwargs):
        media_type = self.determine_media_type(request)
        if media_type is None:
            return HttpResponseNotAcceptable()

        try:
            project = Project.objects.get(id=kwargs["project"])
        except Project.DoesNotExist:
            return HttpResponseNotFound()
        records = project.record_set.all()
        tags = request.GET.get("tags", None)
        if tags:
            records = records.filter(tags__contains=tags)

        content = self.serializer(media_type).encode(project, records, tags, request)
        return HttpResponse(content, content_type="{}; charset=utf-8".format(media_type), status=200)

    @csrf_exempt
    @check_permissions
    def put(self, request, *args, **kwargs):
        project, created = Project.objects.get_or_create(id=kwargs["project"])
        changed = False
        for attr in ("name", "description"):
            if attr in request.data:
                setattr(project, attr, request.data[attr])
                changed = True
        if changed:
            project.save()
        if created:
            project.projectpermission_set.create(user=request.user)
            return HttpResponse('', status=201)  # return newly created project?
        else:
            return HttpResponse('', status=200)


class ProjectListResource(ResourceView):
    preferred_media_type = 'application/vnd.sumatra.project-list-v4+json'
    serializer = ProjectListSerializer

    def get(self, request, *args, **kwargs):
        media_type = self.determine_media_type(request)
        if media_type is None:
            return HttpResponseNotAcceptable()

        # check if the user is authenticated, to set request.user
        auth = AuthenticationDispatcher()
        auth.is_authenticated(request)

        projects = reversed(sorted(Project.objects.filter(
                                    projectpermission__user__username__in=(request.user.username, "anonymous")).distinct(),
                                   key=lambda project: project.last_updated()))
        content = self.serializer(media_type).encode(projects, request)
        return HttpResponse(content, content_type="{}; charset=utf-8".format(media_type), status=200)


class PermissionListResource(ResourceView):
    preferred_media_type = 'application/json'
    serializer = PermissionListSerializer

    @check_permissions
    def get(self, request, *args, **kwargs):
        media_type = self.determine_media_type(request)
        if media_type is None:
            return HttpResponseNotAcceptable()
        try:
            project = Project.objects.get(id=kwargs["project"])
        except Project.DoesNotExist:
            return HttpResponseNotFound()
        content = self.serializer(media_type).encode(project, request)
        return HttpResponse(content, content_type="{}; charset=utf-8".format(media_type), status=200)

    @check_permissions
    def post(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(id=kwargs['project'])
        except Project.DoesNotExist:
            return HttpResponseNotFound()
        form = PermissionsForm(request.POST)
        if form.is_valid():
            project.projectpermission_set.create(user=form.cleaned_data["user"])
            return HttpResponseRedirect(reverse("sumatra-project", args=[project.id]))
        else:
            return HttpResponseBadRequest(form.errors)
