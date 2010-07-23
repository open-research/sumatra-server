from django.forms import ModelForm
from sumatra_piston.models import ProjectPermission

class PermissionsForm(ModelForm):
    class Meta:
        model = ProjectPermission
        fields = ('user',)