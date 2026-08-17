from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.patient_profile, name='patient_profile'),
]