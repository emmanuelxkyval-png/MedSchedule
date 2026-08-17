from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PatientProfile
from .forms import PersonalInfoForm, MedicalProfileForm


@login_required
def patient_profile(request):
    profile, created = PatientProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'personal':
            personal_form = PersonalInfoForm(
                request.POST, instance=request.user
            )
            medical_form = MedicalProfileForm(instance=profile)
            if personal_form.is_valid():
                personal_form.save()
                messages.success(request,
                    'Personal information updated!')
                return redirect('patient_profile')

        elif form_type == 'medical':
            personal_form = PersonalInfoForm(instance=request.user)
            medical_form = MedicalProfileForm(
                request.POST, instance=profile
            )
            if medical_form.is_valid():
                medical_form.save()
                messages.success(request,
                    'Medical profile updated!')
                return redirect('patient_profile')
    else:
        personal_form = PersonalInfoForm(instance=request.user)
        medical_form = MedicalProfileForm(instance=profile)

    return render(request, 'patients/profile.html', {
        'personal_form': personal_form,
        'medical_form': medical_form,
        'profile': profile,
    })