from django.db import models
from employees.models import Employee


# Create your models here.


class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    parent_location = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_locations'
    )

    def __str__(self):
        return self.name


class EquipmentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    STATUS_CHOICES = [
        ('in_use', 'В эксплуатации'),
        ('in_stock', 'На складе'),
        ('under_repair', 'В ремонте'),
        ('written_off', 'Списан'),
    ]

    name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    purchase_date = models.DateField()
    warranty_expire_date = models.DateField(blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    current_owner = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class EquipmentTransfer(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    from_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='transfers_from')
    to_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='transfers_to')
    from_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='transfers_from')
    to_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='transfers_to')
    transfer_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transfer of {self.equipment} on {self.transfer_date}"


class EquipmentWriteOff(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    write_off_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Write-off of {self.equipment} on {self.write_off_date}"
