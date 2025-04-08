from django.contrib import admin
from .models import MaintenancePlan, MaintenanceType, MaintenanceLog
# Register your models here.

admin.site.register(MaintenancePlan)
admin.site.register(MaintenanceType)
admin.site.register(MaintenanceLog)

