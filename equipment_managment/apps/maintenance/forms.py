from django import forms
from django.utils import timezone

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

        if not self.instance.pk:
            self.fields['status'].initial = 'planned'
            self.fields['status'].widget.attrs['class'] = 'disabled'


class CompleteMaintenanceForm(forms.ModelForm):
    parts = forms.ModelMultipleChoiceField(
        queryset=Part.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'select select-bordered select-multiple',
            'data-placeholder': 'Выберите запчасти'
        }),
        required=False
    )

    class Meta:
        model = MaintenanceLog
        fields = ['actual_date', 'result', 'hours_spent', 'parts', 'is_critical', "completed_by"]
        widgets = {
            'actual_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'input input-bordered'
            }),
            'result': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered',
                'rows': 3
            }),
            'hours_spent': forms.NumberInput(attrs={
                'class': 'input input-bordered',
                'step': '0.5',
                'min': '0.5'
            }),
            'is_critical': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'completed_by': forms.Select(
                attrs={
                    'class': 'select select-bordered'
                })
        }

    def __init__(self, *args, **kwargs):
        plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)

        if plan:
            self.fields['parts'].queryset = Part.objects.filter(
                compatible_with=plan.equipment
            )
            self.fields['actual_date'].initial = timezone.now()
