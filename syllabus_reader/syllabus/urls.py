from django.urls import path
from . import views

urlpatterns = [
    # Public landing page
    path('', views.landing_page, name='landing_page'),
    
    # Main navigation views (login required)
    path('curricula/', views.curriculum_list, name='curriculum_list'),
    path('curriculum/<int:curriculum_id>/syllabi/', views.syllabus_list, name='syllabus_list'),
    path('syllabus/<int:syllabus_id>/units/', views.unit_list, name='unit_list'),
    
    # Provider management (admin only)
    path('providers/', views.provider_list, name='provider_list'),
    path('providers/create/', views.create_provider, name='create_provider'),
    path('providers/<int:provider_id>/edit/', views.edit_provider, name='edit_provider'),
    path('providers/<int:provider_id>/delete/', views.delete_provider, name='delete_provider'),
    
    # Create views (admin only)
    path('create/curriculum/', views.create_curriculum, name='create_curriculum'),
    path('curriculum/<int:curriculum_id>/edit/', views.edit_curriculum, name='edit_curriculum'),
    path('create/syllabus/', views.create_syllabus, name='create_syllabus'),
    path('create/syllabus/for-curriculum/<int:curriculum_id>/', views.create_syllabus, name='create_syllabus_for_curriculum'),
    path('syllabus/<int:syllabus_id>/edit/', views.edit_syllabus, name='edit_syllabus'),
    path('create/unit/', views.create_unit, name='create_unit'),
    path('create/unit/for-syllabus/<int:syllabus_id>/', views.create_unit, name='create_unit_for_syllabus'),
    path('unit/<int:unit_id>/edit/', views.edit_unit, name='edit_unit'),
    
    # Legacy compatibility
    path('syllabus/', views.syllabus_view, name='syllabus_view'),
]