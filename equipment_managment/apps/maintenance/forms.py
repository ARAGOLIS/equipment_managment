
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import MaintenancePlan, MaintenanceLog, Part, PartUsage


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
            # Filter status choices to exclude 'in_progress' and 'completed'
            allowed_statuses = [
                ('planned', 'Запланировано')
            ]
            self.fields['status'].choices = allowed_statuses
            self.fields['status'].widget.attrs['disabled'] = 'disabled'
        else:
            # For editing, allowed  statuses
            allowed_statuses = [
                ('planned', 'Запланировано'),
                ('cancelled', 'Отменено')
            ]
            self.fields['status'].choices = allowed_statuses

    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено')
    ]




class MaintenanceLogForm(forms.ModelForm):
    parts = forms.ModelMultipleChoiceField(
        queryset=Part.objects.filter(current_stock__gt=0),
        widget=forms.SelectMultiple(attrs={
            'class': 'select select-bordered select-multiple',
            'data-placeholder': 'Выберите запчасти'
        }),
        required=False
    )

    class Meta:
        model = MaintenanceLog
        fields = [
            'actual_date',
            'completed_by',
            'result',
            'problems_found',
            'recommendations',
            'hours_spent',
            'is_critical',
            'next_service_date',
            'parts'
        ]
        widgets = {
            'actual_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'input input-bordered'
            }),
            'next_service_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered'
            }),
            'result': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered',
                'rows': 4
            }),
            'problems_found': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered',
                'rows': 3
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered',
                'rows': 3
            }),
            'hours_spent': forms.NumberInput(attrs={
                'class': 'input input-bordered',
                'step': '0.1',
                'min': '0'
            }),
            'completed_by': forms.Select(attrs={
                'class': 'select select-bordered'
            }),
            'is_critical': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def __init__(self, *args, **kwargs):
        plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)
        # Set default value for actual_date if not provided
        if not self.instance.pk:
            self.fields['actual_date'].initial = timezone.now()
        # Make completed_by optional in form (model handles default)
        self.fields['completed_by'].required = False
        # Apply input-bordered to any fields without specific widgets
        for field in self.fields:
            if not self.fields[field].widget.attrs.get('class'):
                self.fields[field].widget.attrs['class'] = 'input input-bordered'
        # Filter parts based on plan's equipment compatibility
        if plan and plan.equipment:
            self.fields['parts'].queryset = Part.objects.filter(
                current_stock__gt=0,
                compatible_with=plan.equipment
            )

    def clean(self):
        cleaned_data = super().clean()
        hours_spent = cleaned_data.get('hours_spent')
        if hours_spent and hours_spent < 0:
            self.add_error('hours_spent', 'Hours spent cannot be negative')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Update parts through PartUsage
            if 'parts' in self.cleaned_data:
                # Get existing PartUsage instances
                existing_parts = {pu.part.id: pu for pu in instance.partusage_set.all()}
                selected_parts = self.cleaned_data['parts']

                # Remove PartUsage for parts that were deselected
                for part_id, part_usage in existing_parts.items():
                    if part_id not in [part.id for part in selected_parts]:
                        part_usage.delete()

                # Create or update PartUsage for selected parts
                for part in selected_parts:
                    if part.id not in existing_parts:
                        PartUsage.objects.create(
                            log=instance,
                            part=part,
                            quantity=1  # Default quantity, can be adjusted in formset
                        )
            self.save_m2m()
        return instance


class PartUsageForm(forms.ModelForm):
    class Meta:
        model = PartUsage
        fields = ['part', 'quantity', 'notes']
        widgets = {
            'part': forms.Select(attrs={
                'class': 'select select-bordered'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'input input-bordered',
                'min': 1
            }),
            'notes': forms.TextInput(attrs={
                'class': 'input input-bordered'
            }),
        }

    def __init__(self, *args, **kwargs):
        plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)
        # Filter parts based on plan's equipment compatibility
        if plan and plan.equipment:
            self.fields['part'].queryset = Part.objects.filter(
                current_stock__gt=0,
                compatible_with=plan.equipment
            )
        else:
            self.fields['part'].queryset = Part.objects.filter(current_stock__gt=0)
        # Make part field read-only in formset since it's selected in main form
        self.fields['part'].widget.attrs['disabled'] = True

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        part = self.cleaned_data.get('part')
        if part and quantity > part.current_stock:
            raise forms.ValidationError(
                f"Cannot use {quantity} units. Only {part.current_stock} available in stock."
            )
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity


# Create inline formset for PartUsage
PartUsageFormSet = inlineformset_factory(
    MaintenanceLog,
    PartUsage,
    form=PartUsageForm,
    extra=0,
    can_delete=True,
    fields=('part', 'quantity', 'notes')
)