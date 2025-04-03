from django import forms
from .models import Employee, Department


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'department', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'input input-bordered w-full'})
