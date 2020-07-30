"""
Sumatra Server

:copyright: Copyright 2010-2015 Andrew Davison
:license: BSD 2-clause, see COPYING for details.
"""

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.shortcuts import render
from sumatra.recordstore import serialization


class RecordSerializer(object):
    template = "record_detail.html"

    def __init__(self, media_type):
        self.media_type = media_type

    def encode(self, record, project, request=None):
        if self.media_type in ('application/vnd.sumatra.record-v3+json',
                               'application/vnd.sumatra.record-v4+json',
                               'application/json'):
            # later can add support for multiple versions
            data = serialization.record2dict(record.to_sumatra())
            data['project_id'] = project
            if self.media_type == 'application/vnd.sumatra.record-v3+json':
                for entry in data['output_data']:
                    entry.pop("creation")
            return json.dumps(data, indent=4)
        elif self.media_type == 'text/html':
            context = {"data": record.to_sumatra()}
            return render(request, self.template, context)
        else:
            raise ValueError("Unsupported media type")

    def decode(self, content):
        # content is a JSON string
        return serialization.decode_record(content)


class ProjectSerializer(object):
    template = "project_detail.html"

    def __init__(self, media_type):
        self.media_type = media_type
        self._encoder = DjangoJSONEncoder(ensure_ascii=False, indent=4)

    def encode(self, project, records, tags, request):
        protocol = request.is_secure() and "https" or "http"
        project_uri = "%s://%s%s" % (protocol,
                                     request.get_host(),
                                     reverse("sumatra-project", args=[project.id]))
        data = {
            'id': project.id,
            'name': project.get_name(),
            'description': project.description,
            'records': ["%s%s/" % (project_uri, rec.label)
                        for rec in records],
            'tags': tags,
            'user': request.user.username
        }
        if request.user.username != 'anonymous':
            # avoid non logged-in users harvesting usernames
            data['access'] = [perm.user.username
                              for perm in project.projectpermission_set.all()]
        if self.media_type in ('application/vnd.sumatra.project-v3+json',
                               'application/vnd.sumatra.project-v4+json',
                               'application/json'):
            # later can add support for multiple versions
            return self._encoder.encode(data)
        elif self.media_type == 'text/html':
            context = {"data": data}
            return render(request, self.template, context)
        else:
            raise ValueError("Unsupported media type")


class ProjectListSerializer(object):
    template = "project_list.html"

    def __init__(self, media_type):
        self.media_type = media_type
        self._encoder = DjangoJSONEncoder(ensure_ascii=False)

    def encode(self, projects, request):
        protocol = request.is_secure() and "https" or "http"
        data = [
            {
                "id": project.id,
                "name": project.get_name(),
                "description": project.description,
                "uri": "%s://%s%s" % (protocol,
                                      request.get_host(),
                                      reverse("sumatra-project", args=[project.id])),
                "last_updated": project.last_updated()
            } for project in projects]
        if self.media_type in ('application/vnd.sumatra.project-list-v3+json',
                               'application/vnd.sumatra.project-list-v4+json',
                               'application/json'):
            # later can add support for multiple versions
            return self._encoder.encode(data)
        elif self.media_type == 'text/html':
            context = {"data": data}
            return render(request, self.template, context)
        else:
            raise ValueError("Unsupported media type")


class PermissionListSerializer(object):
    template = "project_permissions.html"

    def __init__(self, media_type):
        self.media_type = media_type
        self._encoder = DjangoJSONEncoder(ensure_ascii=False)

    def encode(self, project, request=None):
        data = {
            'id': project.id,
            'name': project.get_name(),
            'access': [perm.user for perm in project.projectpermission_set.all()],
        }
        if self.media_type == 'application/json':
            return self._encoder.encode(data)
        elif self.media_type == 'text/html':
            context = {"data": data}
            return render(request, self.template, context)
        else:
            raise ValueError("Unsupported media type")