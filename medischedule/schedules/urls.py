from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule_home, name='schedule_home'),
    path('add/', views.add_availability, name='add_availability'),
    path('edit/<int:pk>/', views.edit_availability, name='edit_availability'),
    path('delete/<int:pk>/', views.delete_availability, name='delete_availability'),
    path('break/add/<int:availability_id>/', views.add_break, name='add_break'),
    path('slot/block/<int:slot_id>/', views.block_slot, name='block_slot'),
    path('slot/unblock/<int:slot_id>/', views.unblock_slot, name='unblock_slot'),
    path('daily/', views.daily_schedule, name='daily_schedule'),
    path('daily/<str:target_date>/', views.daily_schedule, name='daily_schedule_date'),
    path('ajax/slots/', views.get_available_slots_ajax, name='ajax_slots'),
    path('ajax/dates/', views.get_available_dates_ajax, name='ajax_dates'),
]