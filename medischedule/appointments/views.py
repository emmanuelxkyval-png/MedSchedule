from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Appointment
from .forms import PatientAppointmentForm, StaffAppointmentForm, ManagerMeetingForm
from accounts.models import User, CLINICAL_ROLES as CLINICAL_STAFF, NON_CLINICAL_ROLES
from schedules.models import AppointmentSlot, MANUAL_CONFIRM_ROLES
from notifications.utils import notify_appointment_booked, notify_manager_meeting
from medischedule.error_handlers import PermissionDeniedError, ValidationError, NotFoundError
NON_CLINICAL_STAFF = NON_CLINICAL_ROLES + ['admin']


@login_required
def book_appointment(request):
    user = request.user

    if user.role in NON_CLINICAL_STAFF:
        raise PermissionDeniedError(
            "IT staff, Admin and Administrative staff "
            "cannot book patient appointments."
        )

    if user.role == 'manager':
        return redirect('manager_meeting')

    if user.role == 'patient':
        form_class = PatientAppointmentForm
        appointment_type = 'patient_clinical'
        if request.method == 'POST':
            form = form_class(request.POST)
        else:
            form = form_class()
    else:
        form_class = StaffAppointmentForm
        appointment_type = 'staff_meeting'
        if request.method == 'POST':
            form = form_class(request.POST, current_user=user)
        else:
            form = form_class(current_user=user)

    if request.method == 'POST':
        if form.is_valid():
            if user.role == 'patient':
                slot = form.cleaned_data['slot']

                if slot.status != 'available':
                    raise ValidationError("This slot is no longer available.")

                staff = form.cleaned_data['staff']
                needs_confirm = staff.role in MANUAL_CONFIRM_ROLES
                status = 'pending' if needs_confirm else 'confirmed'

                with transaction.atomic():
                    appt = Appointment.objects.create(
                        patient=user,
                        doctor=staff,
                        date=slot.date,
                        time=slot.start_time,
                        status=status,
                        reason=form.cleaned_data.get('reason', ''),
                        appointment_type='patient_clinical'
                    )
                    slot.status = 'booked'
                    slot.appointment = appt
                    slot.save()

                notify_appointment_booked(appt)
                if needs_confirm:
                    messages.success(request,
                        f"Appointment requested! "
                        f"{staff.get_full_name() or staff.username} "
                        f"will confirm your appointment soon.")
                else:
                    messages.success(request,
                        "Appointment confirmed! "
                        "Check your email and phone.")
                return redirect('my_appointments')
            else:
                appt = Appointment.objects.create(
                    patient=user,
                    doctor=form.cleaned_data['staff'],
                    date=form.cleaned_data['date'],
                    time=form.cleaned_data['time'],
                    status='confirmed',
                    reason=form.cleaned_data.get('reason', ''),
                    appointment_type='staff_meeting'
                )
                notify_appointment_booked(appt)
                messages.success(request, "Meeting booked!")
                return redirect('my_appointments')
    else:
        # form is already initialized
        pass

    return render(request, 'appointments/book.html', {
        'form': form,
        'is_patient': user.role == 'patient'
    })


@login_required
def my_appointments(request):
    user = request.user
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    if user.role == 'patient':
        appointments = Appointment.objects.filter(patient=user)
    else:
        appointments = (
            Appointment.objects.filter(doctor=user) |
            Appointment.objects.filter(patient=user)
        ).distinct()

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if search_query:
        if user.role == 'patient':
            appointments = appointments.filter(
                doctor__first_name__icontains=search_query
            ) | appointments.filter(
                doctor__last_name__icontains=search_query
            ) | appointments.filter(
                doctor__username__icontains=search_query
            )
        else:
            appointments = appointments.filter(
                patient__first_name__icontains=search_query
            ) | appointments.filter(
                patient__last_name__icontains=search_query
            ) | appointments.filter(
                patient__username__icontains=search_query
            )

    appointments = appointments.order_by('-date', '-time')

    context = {
        'appointments': appointments,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': appointments.count(),
    }
    return render(request, 'appointments/list.html', context)


@login_required
def appointment_detail(request, appt_id):
    """View appointment details."""
    user = request.user
    appt = get_object_or_404(
        Appointment,
        pk=appt_id
    )
    # Only patient or staff involved can view
    if appt.patient != user and appt.doctor != user and not user.is_staff:
        raise PermissionDeniedError("You cannot view this appointment.")

    return render(request, 'appointments/detail.html', {'appt': appt})


@login_required
def confirm_appointment(request, appt_id):
    """Staff confirms a pending appointment."""
    appt = get_object_or_404(Appointment, pk=appt_id)

    if appt.doctor != request.user:
        raise PermissionDeniedError("You cannot confirm this appointment.")

    if appt.status == 'pending':
        appt.status = 'confirmed'
        appt.save()
        from notifications.utils import notify_appointment_status_changed
        notify_appointment_status_changed(appt)
        messages.success(request,
            f"Appointment with "
            f"{appt.patient.get_full_name() or appt.patient.username} confirmed!")
    return redirect('my_appointments')


@login_required
def complete_appointment(request, appt_id):
    """Staff marks appointment as completed."""
    appt = get_object_or_404(Appointment, pk=appt_id)

    if appt.doctor != request.user:
        raise PermissionDeniedError("You cannot complete this appointment.")

    if appt.status == 'confirmed':
        appt.status = 'completed'
        appt.save()
        try:
            if appt.slot:
                appt.slot.status = 'completed'
                appt.slot.save()
        except AppointmentSlot.DoesNotExist:
            pass
        from notifications.utils import notify_appointment_status_changed
        notify_appointment_status_changed(appt)
        messages.success(request,
            f"Appointment with "
            f"{appt.patient.get_full_name() or appt.patient.username} "
            f"marked as completed.")
    return redirect('my_appointments')


@login_required
def cancel_appointment(request, appt_id):
    """Cancel an appointment and free the slot."""
    appt = get_object_or_404(Appointment, pk=appt_id)

    if request.user != appt.patient and request.user != appt.doctor:
        raise PermissionDeniedError("You cannot cancel this appointment.")

    if appt.status not in ['completed', 'cancelled']:
        appt.status = 'cancelled'
        appt.save()
        try:
            if appt.slot:
                appt.slot.status = 'available'
                appt.slot.appointment = None
                appt.slot.save()
        except AppointmentSlot.DoesNotExist:
            pass
        from notifications.utils import notify_appointment_status_changed
        notify_appointment_status_changed(appt)
        messages.success(request, "Appointment cancelled.")
    return redirect('my_appointments')


@login_required
def reschedule_appointment(request, appt_id):
    """Staff proposes a new time for an appointment."""
    appt = get_object_or_404(Appointment, pk=appt_id)

    if appt.doctor != request.user:
        raise PermissionDeniedError("You cannot reschedule this appointment.")

    if appt.status not in ['pending', 'confirmed']:
        raise ValidationError("This appointment cannot be rescheduled.")

    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')

        if new_date and new_time:
            # Free old slot
            try:
                if appt.slot:
                    appt.slot.status = 'available'
                    appt.slot.appointment = None
                    appt.slot.save()
            except AppointmentSlot.DoesNotExist:
                pass

            from datetime import datetime as dt
            appt.date = dt.strptime(new_date, '%Y-%m-%d').date()
            appt.time = dt.strptime(new_time, '%H:%M').time()
            appt.status = 'pending'
            appt.save()

            # Try to book new slot
            new_slot = AppointmentSlot.objects.filter(
                staff=request.user,
                date=appt.date,
                start_time=appt.time,
                status='available'
            ).first()

            if new_slot:
                new_slot.status = 'booked'
                new_slot.appointment = appt
                new_slot.save()

            from notifications.utils import notify_appointment_status_changed
            notify_appointment_status_changed(appt)
            messages.success(request,
                f"Appointment rescheduled to {appt.date} at {appt.time}.")
            return redirect('my_appointments')

    return render(request, 'appointments/reschedule.html', {'appt': appt})


@login_required
def manager_meeting(request):
    if request.user.role != 'manager':
        raise PermissionDeniedError("Only managers can call staff meetings.")

    all_staff = User.objects.exclude(
        role='patient'
    ).exclude(id=request.user.id)

    if request.method == 'POST':
        form = ManagerMeetingForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                created_appointments = []
                for staff in all_staff:
                    appt = Appointment.objects.create(
                        patient=request.user,
                        doctor=staff,
                        date=form.cleaned_data['date'],
                        time=form.cleaned_data['time'],
                        reason=f"{form.cleaned_data['meeting_title']}: "
                               f"{form.cleaned_data['reason']}",
                        appointment_type='manager_meeting',
                        status='confirmed'
                    )
                    created_appointments.append(appt)

            if created_appointments:
                notify_manager_meeting(
                    request.user,
                    all_staff,
                    created_appointments[0]
                )
            messages.success(request,
                f"Meeting scheduled! "
                f"All {all_staff.count()} staff notified.")
            return redirect('my_appointments')
    else:
        form = ManagerMeetingForm()

    return render(request, 'appointments/manager_meeting.html', {
        'form': form,
        'staff_count': all_staff.count(),
        'staff_list': all_staff
    })