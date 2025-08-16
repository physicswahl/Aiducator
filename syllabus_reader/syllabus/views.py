from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import ProviderForm, CurriculumForm, SyllabusForm, UnitForm
from .models import Provider, Curriculum, Syllabus, Unit

def can_modify_syllabus(user):
    """Check if user can modify syllabus (Admins only)"""
    if not user.is_authenticated:
        return False
    try:
        from aigames.models import UserProfile
        return user.profile.can_modify_syllabus
    except (UserProfile.DoesNotExist, AttributeError):
        # Fallback to old system for backward compatibility
        return user.is_superuser or user.groups.filter(name='Admin').exists()

def is_admin(user):
    """Kept for backward compatibility"""
    return can_modify_syllabus(user)

# Public Landing Page
def landing_page(request):
    """Public landing page for non-authenticated users"""
    if request.user.is_authenticated:
        # Redirect based on user role
        try:
            from aigames.models import UserProfile
            if hasattr(request.user, 'profile') and request.user.profile.is_student:
                return redirect('student_dashboard')
            else:
                return redirect('curriculum_list')
        except (UserProfile.DoesNotExist, AttributeError):
            # Fallback to curriculum list for users without profiles
            return redirect('curriculum_list')
    
    context = {
        'total_curricula': Curriculum.objects.count(),
        'total_syllabi': Syllabus.objects.count(),
        'total_units': Unit.objects.count(),
    }
    return render(request, 'syllabus/landing_page.html', context)

# Dashboard/Home Views (Login Required)
@login_required
def curriculum_list(request):
    curricula = Curriculum.objects.all()
    context = {
        'curricula': curricula,
        'is_admin': is_admin(request.user)
    }
    return render(request, 'syllabus/curriculum_list.html', context)

# Provider Views (Admin only)
@login_required
@user_passes_test(is_admin)
def provider_list(request):
    providers = Provider.objects.all()
    context = {
        'providers': providers,
        'is_admin': is_admin(request.user)
    }
    return render(request, 'syllabus/provider_list.html', context)

@login_required
@user_passes_test(is_admin)
def create_provider(request):
    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Provider created successfully!')
            return redirect('provider_list')
    else:
        form = ProviderForm()
    return render(request, 'syllabus/create_provider.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_provider(request, provider_id):
    provider = get_object_or_404(Provider, id=provider_id)
    if request.method == 'POST':
        form = ProviderForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, 'Provider updated successfully!')
            return redirect('provider_list')
    else:
        form = ProviderForm(instance=provider)
    return render(request, 'syllabus/edit_provider.html', {'form': form, 'provider': provider})

@login_required
@user_passes_test(is_admin)
def delete_provider(request, provider_id):
    provider = get_object_or_404(Provider, id=provider_id)
    if request.method == 'POST':
        provider.delete()
        messages.success(request, 'Provider deleted successfully!')
        return redirect('provider_list')
    return render(request, 'syllabus/delete_provider.html', {'provider': provider})

@login_required
def syllabus_list(request, curriculum_id):
    curriculum = get_object_or_404(Curriculum, id=curriculum_id)
    syllabi = Syllabus.objects.filter(curriculum=curriculum)
    context = {
        'curriculum': curriculum,
        'syllabi': syllabi,
        'is_admin': is_admin(request.user)
    }
    return render(request, 'syllabus/syllabus_list.html', context)

@login_required
def unit_list(request, syllabus_id):
    syllabus = get_object_or_404(Syllabus, id=syllabus_id)
    units = Unit.objects.filter(syllabus=syllabus)
    context = {
        'syllabus': syllabus,
        'units': units,
        'is_admin': is_admin(request.user)
    }
    return render(request, 'syllabus/unit_list.html', context)

# Create Views (Admin only)
@login_required
@user_passes_test(is_admin)
def create_curriculum(request):
    if request.method == 'POST':
        form = CurriculumForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curriculum created successfully!')
            return redirect('curriculum_list')
    else:
        form = CurriculumForm()
    return render(request, 'syllabus/create_curriculum.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_curriculum(request, curriculum_id):
    curriculum = get_object_or_404(Curriculum, id=curriculum_id)
    if request.method == 'POST':
        form = CurriculumForm(request.POST, instance=curriculum)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curriculum updated successfully!')
            return redirect('curriculum_list')
    else:
        form = CurriculumForm(instance=curriculum)
    return render(request, 'syllabus/edit_curriculum.html', {'form': form, 'curriculum': curriculum})

@login_required
@user_passes_test(is_admin)
def create_syllabus(request, curriculum_id=None):
    curriculum = None
    if curriculum_id:
        curriculum = get_object_or_404(Curriculum, id=curriculum_id)
    
    if request.method == 'POST':
        form = SyllabusForm(request.POST)
        if form.is_valid():
            syllabus = form.save(commit=False)
            if curriculum and not syllabus.curriculum:
                syllabus.curriculum = curriculum
            syllabus.save()
            messages.success(request, 'Syllabus created successfully!')
            return redirect('syllabus_list', curriculum_id=syllabus.curriculum.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SyllabusForm()
        if curriculum:
            form.fields['curriculum'].initial = curriculum
    
    return render(request, 'syllabus/create_syllabus.html', {'form': form, 'curriculum': curriculum})

@login_required
@user_passes_test(is_admin)
def edit_syllabus(request, syllabus_id):
    syllabus = get_object_or_404(Syllabus, id=syllabus_id)
    if request.method == 'POST':
        form = SyllabusForm(request.POST, instance=syllabus)
        if form.is_valid():
            form.save()
            messages.success(request, 'Syllabus updated successfully!')
            return redirect('syllabus_list', curriculum_id=syllabus.curriculum.id)
    else:
        form = SyllabusForm(instance=syllabus)
    
    return render(request, 'syllabus/edit_syllabus.html', {'form': form, 'syllabus': syllabus})

@login_required
@user_passes_test(is_admin)
def create_unit(request, syllabus_id=None):
    syllabus = None
    if syllabus_id:
        syllabus = get_object_or_404(Syllabus, id=syllabus_id)
    
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, 'Unit created successfully!')
            return redirect('unit_list', syllabus_id=unit.syllabus.id)
    else:
        form = UnitForm()
        if syllabus:
            form.fields['syllabus'].initial = syllabus
    
    return render(request, 'syllabus/create_unit.html', {'form': form, 'syllabus': syllabus})

@login_required
@user_passes_test(is_admin)
def edit_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unit updated successfully!')
            return redirect('unit_list', syllabus_id=unit.syllabus.id)
    else:
        form = UnitForm(instance=unit)
    
    return render(request, 'syllabus/edit_unit.html', {'form': form, 'unit': unit})

# Legacy view for compatibility
def syllabus_view(request):
    if request.user.is_authenticated:
        return redirect('curriculum_list')
    else:
        return redirect('landing_page')