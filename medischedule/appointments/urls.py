from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('my/', views.my_appointments, name='my_appointments'),
    path('detail/<int:appt_id>/', views.appointment_detail, name='appointment_detail'),
    path('confirm/<int:appt_id>/', views.confirm_appointment, name='confirm_appointment'),
    path('complete/<int:appt_id>/', views.complete_appointment, name='complete_appointment'),
    path('cancel/<int:appt_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('reschedule/<int:appt_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('manager-meeting/', views.manager_meeting, name='manager_meeting'),
]