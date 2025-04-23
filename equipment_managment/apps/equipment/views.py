from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db import transaction
import json
from django.utils import timezone
from .models import Equipment, EquipmentTransfer, EquipmentWriteOff, EquipmentCategory, Location
from .forms import EquipmentForm, TransferForm, WriteOffForm


class EquipmentListView(ListView):
    model = Equipment
    template_name = 'equipment/list.html'
    context_object_name = 'equipments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = EquipmentCategory.objects.all()
        context['locations'] = Location.objects.all()
        context['status_choices'] = Equipment.STATUS_CHOICES
        return context


def equipment_create(request):
    if request.method == "POST":
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save()
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        'closeModal': '',
                        'refreshTable': '',
                        'showToast': {
                            'message': f'Оборудование {equipment.name} добавлено',
                            'type': 'success'
                        }
                    })
                }
            )
        return render(request, "equipment/partials/form.html", {
            "form": form,
            "is_edit": False
        })

    form = EquipmentForm()
    return render(request, "equipment/partials/form.html", {
        "form": form,
        "is_edit": False
    })


def equipment_update(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            equipment = form.save()
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        'closeModal': '',
                        'refreshTable': '',
                        'showToast': {
                            'message': f'Оборудование {equipment.name} обновлено',
                            'type': 'success'
                        }
                    })
                }
            )
        return render(request, "equipment/partials/form.html", {
            "form": form,
            "is_edit": True
        })

    form = EquipmentForm(instance=equipment)
    return render(request, "equipment/partials/form.html", {
        "form": form,
        "is_edit": True
    })


@require_http_methods(["DELETE"])
def equipment_delete(request, pk):
    # тут был пост, хз зачем, в нейронке остался ориг, спроси потом зачем он
    # заменил на delete, убрал проверки и все работает, хз
    equipment = get_object_or_404(Equipment, pk=pk)
    EquipmentTransfer.objects.filter(equipment=equipment).delete()
    EquipmentWriteOff.objects.filter(equipment=equipment).delete()
    equipment.delete()
    return HttpResponse(
        status=204,
        headers={
            'HX-Trigger': json.dumps({
                'refreshTable': '',
                'showToast': {
                    'message': f'Оборудование {equipment.name} удалено',
                    'type': 'error'
                }
            })
        }
    )


def equipment_transfer(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)

    if request.method == "POST":

        post_data = request.POST.copy()
        post_data['equipment'] = str(equipment.id)
        post_data['from_location'] = str(equipment.location.id)
        post_data['from_employee'] = str(equipment.current_owner.id)

        form = TransferForm(post_data)

        # ("Данные формы:", request.POST)  # Что фактически пришло на сервер
        if not form.is_valid():
            print("Ошибки валидации:", form.errors.as_json())

            # Конкретные ошибки

        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.equipment = equipment
            transfer.from_location = equipment.location
            transfer.save()

            equipment.location = transfer.to_location
            equipment.save()

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        'closeModal': '',
                        'refreshTable': '',
                        'showToast': {
                            'message': f'Оборудование {equipment.name} передано',
                            'type': 'success'
                        }
                    })
                }
            )

        return render(request, "equipment/partials/transfer_form.html", {
            "form": form,
            "equipment": equipment
        })

    form = TransferForm(initial={
        'equipment': equipment,
        'transfer_date': timezone.now(),
        'from_location': equipment.location
    })
    return render(request, "equipment/partials/transfer_form.html", {
        "form": form,
        "equipment": equipment
    })


def equipment_writeoff(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)

    if request.method == "POST":

        post_data = request.POST.copy()
        post_data['equipment'] = str(equipment.id)

        form = WriteOffForm(post_data)
        #print("Данные формы:", request.POST)  # Что фактически пришло на сервер
        if not form.is_valid():
            print("Ошибки валидации:", form.errors.as_json())
            # Конкретные ошибки

        if form.is_valid():
            writeoff = form.save(commit=False)
            writeoff.equipment = equipment
            writeoff.save()

            equipment.status = 'written_off'
            equipment.save()

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({
                        'closeModal': '',
                        'refreshTable': '',
                        'showToast': {
                            'message': f'Оборудование {equipment.name} списано',
                            'type': 'success'
                        }
                    })
                }
            )
        return render(request, "equipment/partials/writeoff_form.html", {
            "form": form,
            "equipment": equipment
        })

    form = WriteOffForm(initial={
        'equipment': equipment,
        'write_off_date': timezone.now().date()
    })
    return render(request, "equipment/partials/writeoff_form.html", {
        "form": form,
        "equipment": equipment
    })


def equipment_filter(request):
    equipments = Equipment.objects.all()

    if serial_number_query := request.GET.get('serial_number', '').strip():
        # Разбиваем запрос на части (если нужно искать по части номера)
        search_terms = serial_number_query.split()

        # Базовый запрос
        query = Q()

        # Поиск по каждому термину
        for term in search_terms:
            if len(term) >= 2:  # Игнорируем слишком короткие термины
                query &= Q(serial_number__icontains=term)

        equipments = equipments.filter(query)

    if status := request.GET.get('status'):
        equipments = equipments.filter(status=status)

    if category_id := request.GET.get('category'):
        equipments = equipments.filter(category_id=category_id)

    if location_id := request.GET.get('location'):
        equipments = equipments.filter(location_id=location_id)

    return render(request, "equipment/partials/table.html", {
        "equipments": equipments
    })
