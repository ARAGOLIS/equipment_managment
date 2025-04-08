from django.urls import path
from . import views

app_name = "employees"

urlpatterns = [
    path("", views.employee_list, name="list"),
    path("create/", views.employee_create, name="create"),
    path("<int:pk>/update/", views.employee_update, name="update"),
    path("<int:pk>/delete/", views.employee_delete, name="delete"),
    path('filter/', views.employee_filter, name='employee_filter')
]