from django.urls import path
from . import views

app_name = 'overlap'

urlpatterns = [
    # 4-step gameplay views
    path('matchup/<int:matchup_id>/step1/', views.step1, name='step1'),
    path('matchup/<int:matchup_id>/step2/', views.step2, name='step2'),
    path('matchup/<int:matchup_id>/step3/', views.step3, name='step3'),
    path('matchup/<int:matchup_id>/step4/', views.step4, name='step4'),
    
    # Step completion and navigation
    path('matchup/<int:matchup_id>/complete/', views.complete_step, name='complete_step'),
    path('matchup/<int:matchup_id>/reset/', views.reset_game, name='reset_game'),
    
    # Strategy saving
    path('matchup/<int:matchup_id>/save-strategy/', views.save_strategy, name='save_strategy'),
    
    # Click data management (AJAX)
    path('matchup/<int:matchup_id>/save-click/', views.save_click, name='save_click'),
    
    # AJAX endpoints for dynamic updates (if needed)
    path('matchup/<int:matchup_id>/save-data/', views.save_data, name='save_data'),
]
