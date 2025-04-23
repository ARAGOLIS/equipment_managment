from django.db.models import Q
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db import transaction
import json
from django.utils import timezone
from .models import MaintenancePlan, MaintenanceType, MaintenanceLog, Part
from .forms import MaintenancePlanForm, MaintenanceLogForm, PartUsageFormSet


class MaintenancePlanListView(ListView):
    model = MaintenancePlan
    template_name = 'maintenance/list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'equipment', 'maintenance_type', 'assigned_to'
        )

        # Базовая фильтрация
        if status := self.request.GET.get('status'):
            queryset = queryset.filter(status=status)


        if equipment_query := self.request.GET.get('equipment', '').strip():
            search_terms = equipment_query.split()
            query = Q()
            for term in search_terms:
                if len(term) >= 2:
                    query &= Q(equipment__name__icontains=term) | Q(equipment__serial_number__icontains=term)
            queryset = queryset.filter(query)

        if maintenance_type := self.request.GET.get('maintenance_type'):
            queryset = queryset.filter(maintenance_type_id=maintenance_type)

        if assigned_to := self.request.GET.get('assigned_to'):
            queryset = queryset.filter(assigned_to_id=assigned_to)

        return queryset.order_by('planned_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = MaintenancePlan.STATUS_CHOICES
        context['maintenance_types'] = MaintenanceType.objects.all()


        return context


def maintenance_plan_create(request):
    if request.method == "POST":
        form = MaintenancePlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        'closeModal': '',
                        'refreshTable': '',
                        'showToast': {
                            'message': f'План ТО для {plan.equipment.name} создан',
                            'type': 'success'
                        }
                    })
                }
            )
        return render(request, "maintenance/partials/form.html", {"form": form})

    form = MaintenancePlanForm(initial={
        'planned_date': timezone.now().date(),
        'status': 'planned'
    })
    return render(request, "maintenance/partials/form.html", {"form": form})


def maintenance_plan_update(request, pk):
    plan = get_object_or_404(MaintenancePlan, pk=pk)
    if request.method == "POST":
        form = MaintenancePlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        'closeModal': '',
                        'refreshTable': '',
                        'showToast': {
                            'message': f'План ТО обновлён',
                            'type': 'success'
                        }
                    })
                }
            )
        return render(request, "maintenance/partials/form.html", {"form": form})

    form = MaintenancePlanForm(instance=plan)
    return render(request, "maintenance/partials/form.html", {"form": form})


def maintenance_plan_delete(request, pk):
    plan = get_object_or_404(MaintenancePlan, pk=pk)
    if request.method == "POST":
        equipment_name = plan.equipment.name
        plan.delete()
        return HttpResponse(
            status=204,
            headers={
                'HX-Trigger': json.dumps({
                    'refreshTable': '',
                    'showToast': {
                        'message': f'План ТО для {equipment_name} удалён',
                        'type': 'error'
                    }
                })
            }
        )
    return HttpResponse(status=405)


def start_maintenance(request, pk):
    plan = get_object_or_404(MaintenancePlan, pk=pk)
    if plan.status != 'planned':
        return HttpResponse(status=400)

    plan.status = 'in_progress'
    plan.save()

    return HttpResponse(
        status=204,
        headers={'HX-Trigger': json.dumps({
            'refreshTable': '',
            'showToast': {
                'message': f'ТО для {plan.equipment.name} начато',
                'type': 'success'
            }
        })}
    )


@transaction.atomic
def maintenance_log_create(request, pk):
    plan = get_object_or_404(MaintenancePlan, pk=pk)

    if request.method == "POST":
        form = MaintenanceLogForm(request.POST, plan=plan)
        formset = PartUsageFormSet(request.POST, form_kwargs={'plan': plan})

        if form.is_valid() and formset.is_valid():
            log = form.save(commit=False)
            log.plan = plan
            log.save()
            form.save_m2m()  # Save parts
            formset.instance = log
            formset.save()

            # Update plan status to completed
            plan.status = 'completed'
            plan.save()

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        'closeModal': '',
                        'refreshTable': '',
                        'showToast': {
                            'message': f'Лог ТО для {log.plan.equipment.name} создан',
                            'type': 'success'
                        }
                    })
                }
            )
        return render(request, "maintenance/partials/log_form.html", {
            "form": form,
            "formset": formset,
            "plan": plan
        })

    form = MaintenanceLogForm(initial={
        'actual_date': timezone.now()
    }, plan=plan)
    formset = PartUsageFormSet(form_kwargs={'plan': plan})
    return render(request, "maintenance/partials/log_form.html", {
        "form": form,
        "formset": formset,
        "plan": plan
    })




def maintenance_plan_filter(request):
    plans = MaintenancePlan.objects.select_related('equipment', 'maintenance_type', 'assigned_to').all()

    # Фильтр по оборудованию (аналогично фильтру по серийнику)
    if equipment_query := request.GET.get('equipment', '').strip():
        search_terms = equipment_query.split()
        query = Q()
        for term in search_terms:
            if len(term) >= 2:
                query &= Q(equipment__name__icontains=term) | Q(equipment__serial_number__icontains=term)
        plans = plans.filter(query)

    # Фильтр по типу ТО
    if maintenance_type := request.GET.get('maintenance_type'):
        plans = plans.filter(maintenance_type_id=maintenance_type)

    # Фильтр по ответственному

    if assigned_to := request.GET.get('assigned_to', '').strip():
        search_terms = assigned_to.split()
        query = Q()
        for term in search_terms:
            if len(term) >= 2:
                query &= (
                        Q(assigned_to__first_name__icontains=term) |
                        Q(assigned_to__last_name__icontains=term)
                )
        plans = plans.filter(query)

    # Фильтр по статусу
    if status := request.GET.get('status'):
        plans = plans.filter(status=status)

    return render(request, "maintenance/partials/table.html", {
        "plans": plans
    })