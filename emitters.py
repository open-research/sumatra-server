from piston.emitters import Emitter
from django.template import RequestContext
from django.shortcuts import render_to_response

class HTMLEmitter(Emitter):
    """
    HTML emitter.
    """
    def render(self, request):
        context = RequestContext(request, {"data": self.construct()})
        return render_to_response(self.handler.template, context_instance=context)
    
Emitter.register('html', HTMLEmitter, 'text/html; charset=utf-8')