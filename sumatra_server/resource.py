import piston.resource
from piston.emitters import Emitter

available_emitters = dict(
    ((ct.split(";")[0], em)
     for em, (_, ct) in Emitter.EMITTERS.iteritems())
)
print "AVAILABLE:", available_emitters


def get_emitters_from_accept_header(request):
    if 'HTTP_ACCEPT' in request.META:
        accept = request.META['HTTP_ACCEPT']
    elif 'Accept' in request.META:
        accept = request.META['Accept']
    else:
        accept = ""
    possible_emitters = []
    if accept:
        print "ACCEPT:", accept
        accepted_contenttypes = (ct.split(";")[0] for ct in accept.split(","))  # need to handle wild-cards
        for ct in accepted_contenttypes:
            if ct in available_emitters:
                possible_emitters.append(available_emitters[ct])
        print "POSSIBLE:", possible_emitters
    return possible_emitters


def determine_emitter(request, *args, **kwargs):
    if "emitter_format" in kwargs:
        em = kwargs.pop('emitter_format', None)
    elif "format" in request.GET:
        em = request.GET['format']
    else:
        ems = get_emitters_from_accept_header(request)
        em = ems and ems[0] or "json"
    return em


class Resource(piston.resource.Resource):

    def determine_emitter(self, request, *args, **kwargs):
        return determine_emitter(request, *args, **kwargs)
