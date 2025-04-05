from django import forms
from django.utils import timezone
from .models import Equipment, EquipmentTransfer, EquipmentWriteOff


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'
        widgets = {
            'purchase_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'input input-bordered'
                }
            ),
            'warranty_expire_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'input input-bordered'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'textarea textarea-bordered',
                    'rows': 3
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Исключаем статус "Списан" (written_off)
        if 'status' in self.fields:
            self.fields['status'].choices = [
                choice for choice in self.fields['status'].choices
                if choice[0] != 'written_off'
            ]
            self.fields['status'].widget.attrs.update({
                'class': 'select select-bordered'
            })

        for field in self.fields:
            if not self.fields[field].widget.attrs.get('class'):
                self.fields[field].widget.attrs['class'] = 'input input-bordered'


class TransferForm(forms.ModelForm):
    class Meta:
        model = EquipmentTransfer
        fields = ['equipment', 'from_location', 'to_location', 'to_employee', 'reason']
        widgets = {
            'reason': forms.Textarea(
                attrs={
                    'class': 'textarea textarea-bordered',
                    'rows': 3
                }
            )
        }


class WriteOffForm(forms.ModelForm):
    class Meta:
        model = EquipmentWriteOff
        fields = ['equipment', 'write_off_date', 'reason', 'approved_by']
        widgets = {
            'write_off_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'input input-bordered',
                    'value': timezone.now().strftime('%Y-%m-%d')
                }
            ),
            'reason': forms.Textarea(
                attrs={
                    'class': 'textarea textarea-bordered',
                    'rows': 3
                }
            )
        }
