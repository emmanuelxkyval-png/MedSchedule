from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from notifications.utils import notify_account_created


def landing(request):
    if request.user.is_authenticated:
        if request.user.role == 'patient':
            return redirect('patient_dashboard')
        return redirect('dashboard_home')
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                notify_account_created(user)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Account notification error: {e}")
            messages.success(request,
                'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def user_settings(request):
    if request.method == 'POST':
        user = request.user
        user.email_notifications = 'email_notifications' in request.POST
        user.sms_notifications = 'sms_notifications' in request.POST
        user.save()
        messages.success(request, 'Notification preferences saved!')
        return redirect('user_settings')
    return render(request, 'accounts/settings.html')