from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
]