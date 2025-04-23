from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    path('', views.EquipmentListView.as_view(), name='list'),
    path('create/', views.equipment_create, name='create'),
    path('<int:pk>/update/', views.equipment_update, name='update'),
    path('<int:pk>/delete/', views.equipment_delete, name='delete'),
    path('<int:pk>/transfer/', views.equipment_transfer, name='transfer'),
    path('<int:pk>/writeoff/', views.equipment_writeoff, name='writeoff'),
    path('filter/', views.equipment_filter, name='equipment_filter'),
    path('transfers/', views.equipment_transfer_list, name='transfer_list'),
    path('writeoffs/', views.equipment_write_off_list, name='write_off_list')
]