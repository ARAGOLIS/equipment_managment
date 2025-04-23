# dashboard/views.py
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from equipment.models import Equipment, EquipmentTransfer, EquipmentCategory, EquipmentWriteOff
from maintenance.models import MaintenancePlan
from django.db.models import Count

def dashboard_view(request):
    # Ближайшие обслуживания (ближайшая неделя)
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    upcoming_maintenances = MaintenancePlan.objects.filter(
        planned_date=today,
        status="planned"
    ).select_related('equipment', 'maintenance_type', 'assigned_to')

    # Данные для линейного графика: количество обслуживаний по дням
    maintenance_by_day = MaintenancePlan.objects.filter(
        planned_date__range=[today, next_week],
        status="planned"
    ).values('planned_date').annotate(count=Count('id')).order_by('planned_date')
    dates = [today + timedelta(days=i) for i in range(7)]
    maintenance_counts = [0] * 7
    for entry in maintenance_by_day:
        day_index = (entry['planned_date'] - today).days
        maintenance_counts[day_index] = entry['count']
    maintenance_labels = [d.strftime('%d.%m.%Y') for d in dates]
    maintenance_data = maintenance_counts

    # Данные для круговой диаграммы: оборудование по статусу
    recent_writeoffs = EquipmentWriteOff.objects.all().order_by('-write_off_date')[:3]



    # Данные для столбчатой диаграммы: оборудование по категориям
    equipment_by_category = Equipment.objects.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    category_labels = [entry['category__name'] for entry in equipment_by_category]
    category_data = [entry['count'] for entry in equipment_by_category]

    # Последние перемещения оборудования
    recent_transfers = EquipmentTransfer.objects.select_related(
        'equipment', 'from_location', 'to_location', 'from_employee', 'to_employee'
    ).order_by('-transfer_date')[:3]

    context = {
        'upcoming_maintenances': upcoming_maintenances,
        'maintenance_labels': maintenance_labels,
        'maintenance_data': maintenance_data,
        'recent_writeoffs': recent_writeoffs,
        'category_labels': category_labels,
        'category_data': category_data,
        'recent_transfers': recent_transfers,
    }
    return render(request, 'dashboard/list.html', context)