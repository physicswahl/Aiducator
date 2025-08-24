from django.contrib import admin
from django.urls import path, include, reverse
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def favicon_view(request):
    """Redirect favicon.ico requests to the SVG favicon"""
    return redirect(settings.STATIC_URL + 'syllabus/images/favicon.svg')

@login_required
def login_redirect_view(request):
    """Redirect users to appropriate dashboard based on their role"""
    user = request.user
    
    # Check if user has a profile
    if hasattr(user, 'profile'):
        role = user.profile.role
        if role == 'student':
            return redirect('aigames:student_dashboard')
        elif role == 'teacher':
            return redirect('aigames:team_management_dashboard')
        elif role == 'admin':
            return redirect('/syllabus/curricula/')  # Keep this as path since it's in syllabus app
    
    # Default fallback to curricula
    return redirect('/syllabus/curricula/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login-redirect/', login_redirect_view, name='login_redirect'),
    path('syllabus/', include('syllabus.urls')),
    path('aigames/', include('aigames.urls', namespace='aigames')),
    path('phoneme-density/', include('phoneme_density.urls')),
    path('detector/', include('detector.urls')),
    path('overlap/', include('overlap.urls')),
    path('favicon.ico', favicon_view, name='favicon'),
    path('', RedirectView.as_view(url='/syllabus/', permanent=False)),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)