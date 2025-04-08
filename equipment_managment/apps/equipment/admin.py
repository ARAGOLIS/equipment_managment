from django.contrib import admin
from .models import Equipment, EquipmentCategory, EquipmentTransfer, EquipmentWriteOff, Location
# Register your models here.
admin.site.register(Equipment)
admin.site.register(EquipmentCategory)
admin.site.register(EquipmentTransfer)
admin.site.register(EquipmentWriteOff)
admin.site.register(Location)
