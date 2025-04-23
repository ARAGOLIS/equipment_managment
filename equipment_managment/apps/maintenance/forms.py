from django import forms
from .models import MaintenancePlan, MaintenanceType, MaintenanceLog, Part


class MaintenancePlanForm(forms.ModelForm):
    class Meta:
        model = MaintenancePlan
        fields = '__all__'
        widgets = {
            'planned_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'input input-bordered'
                }
            ),
            'status': forms.Select(
                attrs={
                    'class': 'select select-bordered'
                }
            ),
            'equipment': forms.Select(
                attrs={
                    'class': 'select select-bordered'
                }
            ),
            'assigned_to': forms.Select(
                attrs={
                    'class': 'select select-bordered'
                }
            ),
            'maintenance_type': forms.Select(
                attrs={
                    'class': 'select select-bordered'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if not self.fields[field].widget.attrs.get('class'):
                self.fields[field].widget.attrs['class'] = 'input input-bordered'