from datetime import datetime, timedelta, date
from django.utils import timezone
from .models import StaffAvailability, AppointmentSlot


def generate_slots_for_staff(staff, days_ahead=30):
    """
    Generate appointment slots for a staff member for the next
    days_ahead days based on their weekly availability.
    Slots are only created for the specific day of week set.
    """
    today = timezone.localdate()

    day_map = {
        'Mon': 0, 'Tue': 1, 'Wed': 2,
        'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6,
    }

    availabilities = StaffAvailability.objects.filter(
        staff=staff,
        is_active=True
    ).prefetch_related('breaks')

    if not availabilities.exists():
        return 0

    created_count = 0

    for i in range(days_ahead):
        target_date = today + timedelta(days=i)
        weekday = target_date.weekday()

        for avail in availabilities:
            avail_weekday = day_map.get(avail.day)

            # Only generate for the matching day of week
            if avail_weekday != weekday:
                continue

            breaks = list(avail.breaks.all())
            current_dt = datetime.combine(target_date, avail.start_time)
            end_dt = datetime.combine(target_date, avail.end_time)
            duration = timedelta(minutes=avail.slot_duration)

            while current_dt + duration <= end_dt:
                slot_start = current_dt.time()
                slot_end = (current_dt + duration).time()

                # Check if slot overlaps with any break
                is_break = False
                for brk in breaks:
                    if brk.break_start <= slot_start < brk.break_end:
                        is_break = True
                        break

                # Only create if slot doesn't exist yet
                exists = AppointmentSlot.objects.filter(
                    staff=staff,
                    date=target_date,
                    start_time=slot_start
                ).exists()

                if not exists:
                    AppointmentSlot.objects.create(
                        staff=staff,
                        date=target_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        status='break' if is_break else 'available',
                    )
                    created_count += 1

                current_dt += duration

    return created_count


def get_available_slots(staff, target_date):
    """Get all available slots for a staff on a specific date."""
    now = timezone.localtime(timezone.now())
    today = now.date()
    
    slots = AppointmentSlot.objects.filter(
        staff=staff,
        date=target_date,
        status='available'
    )
    
    if target_date == today:
        slots = slots.filter(start_time__gte=now.time())
        
    return slots.order_by('start_time')


def get_available_dates(staff, days_ahead=30):
    """Get all dates that have at least one available slot."""
    from django.db.models import Q
    now = timezone.localtime(timezone.now())
    today = now.date()
    
    available_slots = AppointmentSlot.objects.filter(
        staff=staff,
        status='available'
    ).filter(
        Q(date__gt=today, date__lte=today + timedelta(days=days_ahead)) |
        Q(date=today, start_time__gte=now.time())
    )
    
    available_dates = available_slots.values_list('date', flat=True).distinct()
    return sorted(set(available_dates))


def mark_past_slots_completed():
    """
    Mark all booked slots from past dates as completed.
    Mark all available slots from past dates as expired.
    Called by management command daily.
    """
    today = timezone.localdate()

    # Mark booked past slots as completed
    past_booked = AppointmentSlot.objects.filter(
        date__lt=today,
        status='booked'
    )
    for slot in past_booked:
        slot.status = 'completed'
        slot.save()
        if slot.appointment and slot.appointment.status == 'confirmed':
            slot.appointment.status = 'completed'
            slot.appointment.save()

    # Mark available past slots as expired
    AppointmentSlot.objects.filter(
        date__lt=today,
        status='available'
    ).update(status='completed')

    return past_booked.count()