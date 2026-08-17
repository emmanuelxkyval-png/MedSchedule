from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import date, timedelta
from django.utils import timezone
from .models import StaffAvailability, BreakTime, AppointmentSlot
from .forms import StaffAvailabilityForm, BreakTimeForm
from .utils import generate_slots_for_staff, get_available_slots, get_available_dates
from medischedule.error_handlers import PermissionDeniedError, ValidationError, NotFoundError
from accounts.models import SCHEDULE_ROLES as CLINICAL_STAFF


@login_required
def schedule_home(request):
    """Main schedule page — shows staff their weekly availability and today's appointments."""
    if request.user.role not in CLINICAL_STAFF:
        raise PermissionDeniedError("Only clinical staff can access schedules.")

    availabilities = StaffAvailability.objects.filter(
        staff=request.user
    ).prefetch_related('breaks')

    today = timezone.localdate()
    today_slots = AppointmentSlot.objects.filter(
        staff=request.user,
        date=today
    ).select_related('appointment__patient').order_by('start_time')

    upcoming_slots = AppointmentSlot.objects.filter(
        staff=request.user,
        date__gt=today,
        status='booked'
    ).select_related('appointment__patient').order_by('date', 'start_time')[:10]

    context = {
        'availabilities': availabilities,
        'today_slots': today_slots,
        'upcoming_slots': upcoming_slots,
        'today': today,
    }
    return render(request, 'schedules/schedule_home.html', context)


@login_required
def add_availability(request):
    if request.user.role not in CLINICAL_STAFF:
        raise PermissionDeniedError("Only clinical staff can set availability.")

    existing_days = StaffAvailability.objects.filter(
        staff=request.user
    ).values_list('day', flat=True)

    if request.method == 'POST':
        form = StaffAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.staff = request.user
            availability.save()
            count = generate_slots_for_staff(request.user, days_ahead=30)
            messages.success(request,
                f"Availability for {availability.get_day_display()} saved! "
                f"{count} slots generated for the next 30 days.")
            return redirect('schedule_home')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = StaffAvailabilityForm()

    return render(request, 'schedules/add_availability.html', {
        'form': form,
        'existing_days': list(existing_days)
    })

@login_required
def edit_availability(request, pk):
    """Edit an existing availability."""
    availability = get_object_or_404(
        StaffAvailability, pk=pk, staff=request.user
    )

    if request.method == 'POST':
        form = StaffAvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            # Regenerate slots
            AppointmentSlot.objects.filter(
                staff=request.user,
                date__gte=timezone.localdate(),
                status='available'
            ).delete()
            generate_slots_for_staff(request.user, days_ahead=30)
            messages.success(request, "Availability updated and slots regenerated!")
            return redirect('schedule_home')
    else:
        form = StaffAvailabilityForm(instance=availability)

    return render(request, 'schedules/add_availability.html', {
        'form': form,
        'editing': True,
        'availability': availability
    })


@login_required
def delete_availability(request, pk):
    """Delete an availability day."""
    availability = get_object_or_404(
        StaffAvailability, pk=pk, staff=request.user
    )
    day = availability.get_day_display()
    availability.delete()
    AppointmentSlot.objects.filter(
        staff=request.user,
        date__gte=timezone.localdate(),
        status='available'
    ).delete()
    messages.success(request, f"{day} availability removed.")
    return redirect('schedule_home')


@login_required
def add_break(request, availability_id):
    """Add a break time to an availability."""
    availability = get_object_or_404(
        StaffAvailability, pk=availability_id, staff=request.user
    )

    if request.method == 'POST':
        form = BreakTimeForm(request.POST)
        if form.is_valid():
            brk = form.save(commit=False)
            brk.availability = availability
            brk.save()
            AppointmentSlot.objects.filter(
                staff=request.user,
                date__gte=timezone.localdate(),
                status='available',
                start_time__gte=brk.break_start,
                start_time__lt=brk.break_end
            ).update(status='break')
            messages.success(request, f"Break '{brk.label}' added.")
            return redirect('schedule_home')
    else:
        form = BreakTimeForm()

    return render(request, 'schedules/add_break.html', {
        'form': form,
        'availability': availability
    })


@login_required
def block_slot(request, slot_id):
    """Block a specific slot."""
    slot = get_object_or_404(
        AppointmentSlot, pk=slot_id, staff=request.user
    )
    if slot.status == 'available':
        slot.status = 'blocked'
        slot.save()
        messages.success(request, f"Slot {slot.start_time} blocked.")
    return redirect('schedule_home')


@login_required
def unblock_slot(request, slot_id):
    """Unblock a specific slot."""
    slot = get_object_or_404(
        AppointmentSlot, pk=slot_id, staff=request.user
    )
    if slot.status == 'blocked':
        slot.status = 'available'
        slot.save()
        messages.success(request, f"Slot {slot.start_time} unblocked.")
    return redirect('schedule_home')


@login_required
def daily_schedule(request, target_date=None):
    """View all slots for a specific date."""
    if target_date:
        from datetime import datetime
        view_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    else:
        view_date = timezone.localdate()

    slots = AppointmentSlot.objects.filter(
        staff=request.user,
        date=view_date
    ).select_related('appointment__patient').order_by('start_time')

    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    return render(request, 'schedules/daily_schedule.html', {
        'slots': slots,
        'view_date': view_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': timezone.localdate(),
    })


@login_required
def get_available_slots_ajax(request):
    """AJAX endpoint — returns available slots for a staff on a date."""
    staff_id = request.GET.get('staff_id')
    date_str = request.GET.get('date')

    if not staff_id or not date_str:
        return JsonResponse({'slots': []})

    try:
        from accounts.models import User
        from datetime import datetime
        staff = User.objects.get(pk=staff_id)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        slots = get_available_slots(staff, target_date)
        slots_data = []
        for slot in slots:
            start_str = slot.start_time.strftime('%I:%M %p')
            if start_str.startswith('0'):
                start_str = start_str[1:]
            end_str = slot.end_time.strftime('%I:%M %p')
            if end_str.startswith('0'):
                end_str = end_str[1:]
            
            slots_data.append({
                'id': slot.id,
                'start_time': start_str,
                'end_time': end_str,
                'slot_type': slot.slot_type,
            })
        return JsonResponse({'slots': slots_data})
    except Exception as e:
        return JsonResponse({'slots': [], 'error': str(e)})


@login_required
def get_available_dates_ajax(request):
    """AJAX endpoint — returns dates with available slots for a staff."""
    staff_id = request.GET.get('staff_id')

    if not staff_id:
        return JsonResponse({'dates': []})

    try:
        from accounts.models import User
        staff = User.objects.get(pk=staff_id)
        available_dates = get_available_dates(staff)
        return JsonResponse({
            'dates': [d.strftime('%Y-%m-%d') for d in available_dates]
        })
    except Exception as e:
        return JsonResponse({'dates': [], 'error': str(e)})