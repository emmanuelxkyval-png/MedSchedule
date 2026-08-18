import requests
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import get_connection
from .models import Notification

logger = logging.getLogger(__name__)


# ─── IN-APP NOTIFICATION ──────────────────────────────────────────────────────

def create_notification(user, message):
    Notification.objects.create(user=user, message=message)


# ─── EMAIL NOTIFICATION ───────────────────────────────────────────────────────

def send_email_notification(user, subject, message):
    if not user.email:
        return
    try:
        connection = get_connection(timeout=10)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
            connection=connection,
        )
    except Exception as e:
        logger.error(f"Email failed for {user.email}: {e}")


# ─── SMS NOTIFICATION (TERMII) ────────────────────────────────────────────────

def send_sms_notification(user, message):
    if not user.phone:
        return
    phone = user.phone.replace('+', '')
    payload = {
        "to": phone,
        "from": settings.TERMII_SENDER_ID,
        "sms": message,
        "type": "plain",
        "channel": "generic",
        "api_key": settings.TERMII_API_KEY,
    }
    try:
        response = requests.post(
            settings.TERMII_BASE_URL,
            json=payload,
            timeout=10
        )
        if response.status_code != 200:
            logger.error(f"SMS failed for {phone}: {response.text}")
    except Exception as e:
        logger.error(f"SMS error for {phone}: {e}")


# ─── BROWSER PUSH NOTIFICATION ────────────────────────────────────────────────

def send_push_notification(user, title, message):
    try:
        from webpush import send_user_notification
        payload = {
            'head': title,
            'body': message,
        }
        send_user_notification(
            user=user,
            payload=payload,
            ttl=1000
        )
    except ImportError:
        logger.error("webpush send_user_notification not available")
    except Exception as e:
        logger.error(f"Push notification failed for {user.username}: {e}")


# ─── COMBINED NOTIFICATION ────────────────────────────────────────────────────

def notify_user(user, subject, message, sms_message=None):
    create_notification(user, message)
    if getattr(user, 'email_notifications', True):
        send_email_notification(user, subject, message)
    if getattr(user, 'sms_notifications', True):
        send_sms_notification(user, sms_message or message)
    send_push_notification(user, subject, message)


# ─── SPECIFIC NOTIFICATION EVENTS ────────────────────────────────────────────

def notify_account_created(user):
    site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    subject = "Welcome to MediSchedule!"
    message = (
        f"Hello {user.get_full_name() or user.username},\n\n"
        f"Your MediSchedule account has been created successfully.\n"
        f"Username: {user.username}\n"
        f"Role: {user.role.title()}\n\n"
        f"You can now log in at {site_url}/accounts/login/\n\n"
        f"Welcome aboard!\n"
        f"— MediSchedule Team"
    )
    sms = (
        f"Welcome to MediSchedule! "
        f"Your account ({user.username}) has been created. "
        f"Login at {site_url}"
    )
    notify_user(user, subject, message, sms)


def notify_appointment_booked(appointment):
    patient = appointment.patient
    doctor = appointment.doctor

    subject = "Appointment Booked – MediSchedule"
    message = (
        f"Hello {patient.get_full_name() or patient.username},\n\n"
        f"Your appointment has been booked successfully.\n"
        f"With: {doctor.get_full_name() or doctor.username}\n"
        f"Date: {appointment.date}\n"
        f"Time: {appointment.time}\n"
        f"Status: {appointment.status.title()}\n\n"
        f"— MediSchedule Team"
    )
    sms = (
        f"MediSchedule: Appointment booked with "
        f"{doctor.get_full_name() or doctor.username} "
        f"on {appointment.date} at {appointment.time}."
    )
    notify_user(patient, subject, message, sms)

    doc_subject = "New Appointment – MediSchedule"
    doc_message = (
        f"Hello {doctor.get_full_name() or doctor.username},\n\n"
        f"A new appointment has been scheduled with you.\n"
        f"Patient: {patient.get_full_name() or patient.username}\n"
        f"Date: {appointment.date}\n"
        f"Time: {appointment.time}\n"
        f"Reason: {appointment.reason or 'Not specified'}\n\n"
        f"— MediSchedule Team"
    )
    doc_sms = (
        f"MediSchedule: New appointment from "
        f"{patient.get_full_name() or patient.username} "
        f"on {appointment.date} at {appointment.time}."
    )
    notify_user(doctor, doc_subject, doc_message, doc_sms)


def notify_appointment_status_changed(appointment):
    patient = appointment.patient
    doctor = appointment.doctor
    status = appointment.status.title()

    subject = f"Appointment {status} – MediSchedule"
    message = (
        f"Hello {patient.get_full_name() or patient.username},\n\n"
        f"Your appointment status has been updated.\n"
        f"With: {doctor.get_full_name() or doctor.username}\n"
        f"Date: {appointment.date}\n"
        f"Time: {appointment.time}\n"
        f"New Status: {status}\n\n"
        f"— MediSchedule Team"
    )
    sms = (
        f"MediSchedule: Your appointment on {appointment.date} "
        f"at {appointment.time} is now {status}."
    )
    notify_user(patient, subject, message, sms)


def notify_manager_meeting(manager, staff_list, appointment):
    subject = "Staff Meeting Called – MediSchedule"
    for staff in staff_list:
        message = (
            f"Hello {staff.get_full_name() or staff.username},\n\n"
            f"A staff meeting has been called by "
            f"{manager.get_full_name() or manager.username}.\n"
            f"Date: {appointment.date}\n"
            f"Time: {appointment.time}\n"
            f"Agenda: {appointment.reason}\n\n"
            f"Please be available.\n"
            f"— MediSchedule Team"
        )
        sms = (
            f"MediSchedule: Staff meeting by manager on "
            f"{appointment.date} at {appointment.time}. "
            f"Agenda: {appointment.reason[:50]}"
        )
        notify_user(staff, subject, message, sms)


def notify_schedule_reminder(schedule):
    doctor = schedule.doctor
    subject = "Schedule Reminder – MediSchedule"
    message = (
        f"Hello {doctor.get_full_name() or doctor.username},\n\n"
        f"Reminder about your schedule today.\n"
        f"Day: {schedule.get_day_display()}\n"
        f"Start Time: {schedule.start_time}\n"
        f"End Time: {schedule.end_time}\n\n"
        f"— MediSchedule Team"
    )
    sms = (
        f"MediSchedule: Your schedule today is "
        f"{schedule.start_time} to {schedule.end_time}."
    )
    notify_user(doctor, subject, message, sms)