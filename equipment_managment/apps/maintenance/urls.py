from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.MaintenancePlanListView.as_view(), name='plan_list'),
    path('plans/create/', views.maintenance_plan_create, name='plan_create'),
    path('plans/<int:pk>/update/', views.maintenance_plan_update, name='plan_update'),
    path('plans/<int:pk>/delete/', views.maintenance_plan_delete, name='plan_delete'),
    path('filter/', views.maintenance_plan_filter, name='plan_filter')

    # Дополнительные маршруты для других сущностей
    #path('types/', views.maintenance_type_list, name='type_list'),
    #path('logs/', views.maintenance_log_list, name='log_list'),
]