from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from appointments.models import Appointment
from accounts.models import User, SCHEDULE_ROLES as CLINICAL_STAFF, NON_CLINICAL_ROLES as NON_CLINICAL_STAFF
from patients.models import PatientProfile


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return render(request, 'home.html')


@login_required
def dashboard_home(request):
    user = request.user

    if user.role == 'patient':
        return redirect('patient_dashboard')

    if user.role in CLINICAL_STAFF:
        return redirect('staff_dashboard')

    if user.role in NON_CLINICAL_STAFF:
        return redirect('staff_dashboard')

    # Admin/Manager dashboard
    total_appointments = Appointment.objects.count()
    total_patients = User.objects.filter(role='patient').count()
    total_staff = User.objects.exclude(role='patient').count()
    recent_appointments = Appointment.objects.select_related(
        'patient', 'doctor'
    ).order_by('-created_at')[:10]
    pending_count = Appointment.objects.filter(status='pending').count()
    confirmed_count = Appointment.objects.filter(status='confirmed').count()
    completed_count = Appointment.objects.filter(status='completed').count()
    cancelled_count = Appointment.objects.filter(status='cancelled').count()
    staff_by_role = []
    staff_roles = [
        'doctor', 'nurse', 'pharmacist', 'lab_scientist',
        'radiologist', 'physiotherapist', 'dentist',
        'surgeon', 'anesthetist', 'dietitian',
        'receptionist', 'admin_staff', 'it_staff', 'manager'
    ]
    for role in staff_roles:
        count = User.objects.filter(role=role).count()
        if count > 0:
            staff_by_role.append({
                'role': role.replace('_', ' ').title(),
                'count': count
            })
    context = {
        'total_appointments': total_appointments,
        'total_patients': total_patients,
        'total_staff': total_staff,
        'recent_appointments': recent_appointments,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'staff_by_role': staff_by_role,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def staff_dashboard(request):
    if request.user.role not in CLINICAL_STAFF + NON_CLINICAL_STAFF:
        return redirect('dashboard_home')

    user = request.user
    today = timezone.localdate()
    from datetime import date
    month_start = date(today.year, today.month, 1)

    # Today's appointments
    today_appointments = Appointment.objects.filter(
        doctor=user,
        date=today
    ).select_related('patient').order_by('time')

    # Pending confirmations
    pending_appointments = Appointment.objects.filter(
        doctor=user,
        status='pending'
    ).select_related('patient').order_by('date', 'time')

    # Monthly appointments
    monthly_appointments = Appointment.objects.filter(
        doctor=user,
        date__gte=month_start
    )

    # Total appointments ever
    total_appointments = Appointment.objects.filter(
        doctor=user
    ).count()

    # Completed this month
    completed_month = monthly_appointments.filter(
        status='completed'
    ).count()

    # Upcoming appointments not today
    upcoming_appointments = Appointment.objects.filter(
        doctor=user,
        date__gt=today,
        status__in=['pending', 'confirmed']
    ).select_related('patient').order_by('date', 'time')[:5]

    # Today's slots from schedule
    from schedules.models import AppointmentSlot, StaffAvailability
    today_slots = AppointmentSlot.objects.filter(
        staff=user,
        date=today
    ).select_related('appointment__patient').order_by('start_time')

    # Availability summary
    availabilities = StaffAvailability.objects.filter(
        staff=user,
        is_active=True
    )
    available_days = list(
        availabilities.values_list('day', flat=True)
    )
    all_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    # Recent unread notifications
    from notifications.models import Notification
    recent_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).order_by('-created_at')[:5]

    context = {
        'today': today,
        'today_appointments': today_appointments,
        'today_count': today_appointments.count(),
        'pending_appointments': pending_appointments,
        'pending_count': pending_appointments.count(),
        'total_appointments': total_appointments,
        'completed_month': completed_month,
        'upcoming_appointments': upcoming_appointments,
        'today_slots': today_slots,
        'available_days': available_days,
        'all_days': all_days,
        'recent_notifications': recent_notifications,
        'is_clinical': user.role in CLINICAL_STAFF,
    }
    return render(request, 'dashboard/staff_dashboard.html', context)


@login_required
def patient_dashboard(request):
    if request.user.role != 'patient':
        return redirect('dashboard_home')

    user = request.user
    today = timezone.localdate()

    all_appointments = Appointment.objects.filter(
        patient=user
    ).order_by('date', 'time')

    total = all_appointments.count()
    upcoming = all_appointments.filter(
        date__gte=today,
        status__in=['pending', 'confirmed']
    )
    completed = all_appointments.filter(status='completed')
    cancelled = all_appointments.filter(status='cancelled')
    next_appointment = upcoming.first()
    past_appointments = all_appointments.filter(
        date__lt=today
    ).order_by('-date')[:5]

    try:
        profile = user.patient_profile
    except PatientProfile.DoesNotExist:
        profile = None

    profile_fields = {
        'First Name': bool(user.first_name),
        'Last Name': bool(user.last_name),
        'Email': bool(user.email),
        'Phone': bool(user.phone),
        'Gender': bool(user.gender),
        'Date of Birth': bool(user.date_of_birth),
        'Address': bool(user.address),
        'Blood Group': bool(profile and profile.blood_group),
        'Emergency Contact': bool(
            profile and profile.emergency_contact_phone
        ),
        'Medical History': bool(profile and profile.medical_history),
    }
    completed_fields = sum(profile_fields.values())
    total_fields = len(profile_fields)
    profile_percent = int((completed_fields / total_fields) * 100)
    missing_fields = [k for k, v in profile_fields.items() if not v]

    context = {
        'today': today,
        'total': total,
        'upcoming': upcoming,
        'upcoming_count': upcoming.count(),
        'completed_count': completed.count(),
        'cancelled_count': cancelled.count(),
        'next_appointment': next_appointment,
        'past_appointments': past_appointments,
        'profile_percent': profile_percent,
        'missing_fields': missing_fields,
        'profile': profile,
    }
    return render(request, 'dashboard/patient_dashboard.html', context)