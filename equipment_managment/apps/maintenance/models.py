from django.db import models
from django.utils import timezone

from employees.models import Employee
from equipment.models import Equipment


class MaintenanceType(models.Model):
    name = models.CharField(max_length=100)  # "ТО-1", "Диагностика двигателя"
    description = models.TextField()  # Подробное описание процедуры
    interval_days = models.PositiveIntegerField()  # 90 (для ТО-3 раз в 3 месяца)

    def __str__(self):
        return self.name


class MaintenancePlan(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено')
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)  # Какое оборудование
    maintenance_type = models.ForeignKey(MaintenanceType, on_delete=models.PROTECT)  # Что нужно сделать
    planned_date = models.DateField()  # Когда планируется
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)  # Кто отвечает
    status = models.CharField(choices=STATUS_CHOICES)


class MaintenanceLog(models.Model):
    plan = models.OneToOneField(MaintenancePlan, on_delete=models.CASCADE, related_name='log')
    actual_date = models.DateTimeField(default=timezone.now)
    completed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='completed_maintenance')
    result = models.TextField(verbose_name="Результаты работы")
    problems_found = models.TextField(blank=True, verbose_name="Выявленные проблемы")
    recommendations = models.TextField(blank=True, verbose_name="Рекомендации")
    hours_spent = models.DecimalField(max_digits=5, decimal_places=1, verbose_name="Затрачено часов")
    parts_used = models.ManyToManyField('Part', through='PartUsage', blank=True)
    is_critical = models.BooleanField(default=False, verbose_name="Критичные неисправности")
    next_service_date = models.DateField(null=True, blank=True, verbose_name="Рекомендуемая дата следующего ТО")

    class Meta:
        verbose_name = "Лог ТО"
        verbose_name_plural = "Логи ТО"

    def save(self, *args, **kwargs):
        if not self.completed_by:
            self.completed_by = self.plan.assigned_to
        super().save(*args, **kwargs)


class Part(models.Model):
    PART_TYPES = [
        ('consumable', 'Расходник'),
        ('spare', 'Запчасть'),
        ('tool', 'Инструмент'),
        ('other', 'Прочее')
    ]

    name = models.CharField(max_length=100, verbose_name="Наименование")
    part_type = models.CharField(max_length=20, choices=PART_TYPES, default='spare')
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name="Инвентарный номер")
    compatible_with = models.ManyToManyField(Equipment, blank=True, verbose_name="Совместимость")
    current_stock = models.PositiveIntegerField(default=0, verbose_name="Остаток на складе")
    min_stock_level = models.PositiveIntegerField(default=1, verbose_name="Минимальный запас")
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Стоимость единицы")
    location = models.CharField(max_length=50, blank=True, verbose_name="Место хранения")
    supplier_info = models.JSONField(default=dict, blank=True, verbose_name="Информация о поставщике")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    class Meta:
        verbose_name = "Запчасть"
        verbose_name_plural = "Запчасти"

    def __str__(self):
        return f"{self.name} ({self.inventory_number})"

    @property
    def needs_restock(self):
        return self.current_stock <= self.min_stock_level


class PartUsage(models.Model):
    log = models.ForeignKey(MaintenanceLog, on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Использование запчасти"
        verbose_name_plural = "Использование запчастей"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Автоматическое обновление остатков
        self.part.current_stock -= self.quantity
        self.part.save()


