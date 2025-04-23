from django.contrib import admin
from .models import MaintenancePlan, MaintenanceType, MaintenanceLog, Part, PartUsage
# Register your models here.

admin.site.register(MaintenancePlan)
admin.site.register(MaintenanceType)
admin.site.register(MaintenanceLog)
admin.site.register(Part)
admin.site.register(PartUsage)

