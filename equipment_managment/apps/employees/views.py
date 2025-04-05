from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django.http import JsonResponse, HttpResponse
from .models import Employee, Department
from .forms import EmployeeForm
import json

class EmployeeListView(ListView):
    model = Employee
    template_name = "employees/list.html"
    context_object_name = "employees"

    def get_queryset(self):
        queryset = super().get_queryset()
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department__id=department)
        return queryset


def employee_list(request):
    employees = Employee.objects.all()
    department_id = request.GET.get('department')

    if department_id:
        employees = employees.filter(department_id=department_id)

    if request.headers.get('HX-Request'):
        # Возвращаем только таблицу для HTMX-запросов
        return render(request, 'employees/partials/employee_table.html', {
            'employees': employees
        })

    # Полный рендеринг для обычных запросов
    return render(request, 'employees/list.html', {
        'employees': employees,
        'departments': Department.objects.all()
    })


def employee_create(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        try:
            if form.is_valid():
                employee = form.save()
                return HttpResponse(
                    status=204,
                    headers={
                        'HX-Trigger': json.dumps({
                            'closeModal': '',
                            'refreshTable': '',
                            'showToast': {
                                'message': f'Сотрудник {employee.first_name} {employee.last_name} добавлен',
                                'type': 'success'
                            }
                        })
                    }
                )
            return render(request, "employees/partials/form.html", {
                "form": form
            })

        except ValidationError as e:
            if 'email' in e.message_dict:
                return JsonResponse(
                    {'email_error': 'Email уже существует'},
                    status=400
                )
            return render(request, "employees/partials/form.html", {"form": form})

    form = EmployeeForm()
    return render(request, "employees/partials/form.html", {"form": form})


def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        try:
            if form.is_valid():
                form.save()
                return HttpResponse(
                    status=204,
                    headers={
                        'HX-Trigger': json.dumps({
                            'closeModal': '',
                            'refreshTable': '',
                            'showToast': f'Данные сотрудника {employee.first_name} {employee.last_name} обновлены',

                        })
                    }
                )
            return render(request, "employees/partials/form.html", {
                "form": form,
                "is_edit": True
            })

        except ValidationError as e:
            if 'email' in e.message_dict:
                return JsonResponse(
                    {'email_error': 'Email уже используется другим сотрудником'},
                    status=400
                )
            return render(request, "employees/partials/form.html", {
                "form": form,
                "is_edit": True
            })

    form = EmployeeForm(instance=employee)
    return render(request, "employees/partials/form.html", {
        "form": form,
        "is_edit": True
    })


@require_http_methods(["DELETE"])
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.delete()
    return HttpResponse(
        status=204,
        headers={
            'HX-Trigger': json.dumps({
                'refreshTable': '',
                'showToast': f'Сотрудник {employee.first_name} {employee.last_name} успешно удален',

            })
        }
    )  # HTMX удалит строку автоматически


def employee_filter(request):
    #employees = Employee.objects.all()

    # Фильтр по имени (безопасный поиск)
    employees = Employee.objects.annotate(
        full_name=Concat(
            'last_name', Value(' '), 'first_name',
            output_field=models.CharField()
        )
    )

    # Фильтр по ФИО
    if search_query := request.GET.get('full_name', '').strip():
        search_terms = search_query.split()

        # Базовый запрос
        query = Q()

        # Поиск по каждому термину
        for term in search_terms:
            if len(term) >= 2:  # Игнорируем слишком короткие термины
                query &= (
                        Q(full_name__icontains=term) |
                        Q(first_name__icontains=term) |
                        Q(last_name__icontains=term)
                )

        employees = employees.filter(query)

    if department := request.GET.get('department'):
        employees = employees.filter(department_id=department)

    if position := request.GET.get('position'):
        employees = employees.filter(position_id=position)

    return render(request, "employees/partials/employee_table.html", {
        "employees": employees
    })
