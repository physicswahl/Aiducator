from django.urls import path
from . import views

app_name = 'phoneme_density'

urlpatterns = [
    # Matchup-based gameplay views
    path('matchup/<int:matchup_id>/step1/', views.step1, name='step1'),
    path('matchup/<int:matchup_id>/step2/', views.step2, name='step2'),
    path('matchup/<int:matchup_id>/step3/', views.step3, name='step3'),
    path('matchup/<int:matchup_id>/step4/', views.step4, name='step4'),
    path('matchup/<int:matchup_id>/step5/', views.step5, name='step5'),
    path('matchup/<int:matchup_id>/step6/', views.step6, name='step6'),
    
    # Step completion for teachers
    path('matchup/<int:matchup_id>/complete-step/<int:step_number>/', views.complete_matchup_step, name='complete_matchup_step'),
    
    # Simple step completion for testing
    path('matchup/<int:matchup_id>/mark-step-complete/<int:step_number>/', views.mark_step_complete, name='mark_step_complete'),
    
    # PDF exports
    path('matchup/<int:matchup_id>/step1/export-pdf/', views.export_step1_pdf, name='export_step1_pdf'),
    
    # Text analysis
    path('matchup/<int:matchup_id>/text/<int:text_number>/analysis/', views.text_analysis, name='text_analysis'),
]
