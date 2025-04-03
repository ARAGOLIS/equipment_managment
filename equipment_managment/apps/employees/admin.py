from django.contrib import admin

# Register your models here.
from .models import Employee, Department
# Register your models here.
admin.site.register(Employee)
admin.site.register(Department)