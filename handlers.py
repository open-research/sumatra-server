from piston.handler import BaseHandler
from sumatra.recordstore.django_store import models
import datetime

one_second = datetime.timedelta(0, 1)

class RecordHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')
    model = models.SimulationRecord
    fields = ('project', 'group', 'timestamp', 'reason', 'outcome', 'duration',
              'executable', 'repository', 'main_file', 'version', 'diff',
              'dependencies', 'parameters', 'launch_mode', 'datastore',
              'data_key', 'platforms', 'tags')
    
    def read(self, request, project, group, year, month, day, hour, minute, second):
        D = {}
        for key in 'year', 'month', 'day', 'hour', 'minute', 'second':
            D[key] = int(locals()[key])
        timestamp = datetime.datetime(**D)
        return BaseHandler.read(self, request,
                                project=project, group=group,
                                timestamp__gte=timestamp,
                                timestamp__lt=timestamp + one_second)
    

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