"""
Sumatra Server

:copyright: Copyright 2010-2014 Andrew Davison
:license: CeCILL, see COPYING for details.
"""

from piston.emitters import Emitter, JSONEmitter
from piston.utils import Mimer
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils import simplejson


class HTMLEmitter(Emitter):
    """
    HTML emitter.
    """

    def render(self, request):
        context = RequestContext(request, {"data": self.construct()})
        return render_to_response(self.handler.template, context_instance=context)

Emitter.register('html', HTMLEmitter, 'text/html; charset=utf-8')


class SumatraRecordJSONEmitter(JSONEmitter):
    pass


class SumatraProjectJSONEmitter(JSONEmitter):
    pass


class SumatraProjectListJSONEmitter(JSONEmitter):
    pass


Emitter.register('record-v3+json', SumatraRecordJSONEmitter, 'application/vnd.sumatra.record-v3+json; charset=utf-8')
Emitter.register('project-v3+json', SumatraRecordJSONEmitter, 'application/vnd.sumatra.project-v3+json; charset=utf-8')
Emitter.register('project-list-v3+json', SumatraRecordJSONEmitter,
                 'application/vnd.sumatra.project-list-v3+json; charset=utf-8')

Mimer.register(simplejson.loads, ('application/vnd.sumatra.record-v3+json',
                                  'application/vnd.sumatra.project-v3+json',
                                  'application/vnd.sumatra.project-list-3+json',
                                  'application/json'))

# really need to tie emitter to handler or resource, as these are resource-specific media types, but for now we
# just accept everything
