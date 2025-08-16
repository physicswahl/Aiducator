from django.urls import path
from . import views

urlpatterns = [
    # Student Dashboard
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Team URLs
    path('teams/', views.list_teams, name='list_teams'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    
    # Team Management URLs (for teachers)
    path('team-management/', views.team_management_dashboard, name='team_management_dashboard'),
    path('team-management/teams/', views.school_teams_list, name='school_teams_list'),
    path('team-management/teams/create/', views.create_school_team, name='create_school_team'),
    path('team-management/teams/<int:team_id>/', views.school_team_detail, name='school_team_detail'),
    path('team-management/teams/<int:team_id>/edit/', views.edit_school_team, name='edit_school_team'),
    path('team-management/teams/<int:team_id>/delete/', views.delete_school_team, name='delete_school_team'),
    
    # Game Matchup URLs
    path('matchups/', views.game_matchups_list, name='game_matchups_list'),
    path('matchups/create/', views.create_game_matchup, name='create_game_matchup'),
    path('matchups/<int:matchup_id>/', views.game_matchup_detail, name='game_matchup_detail'),
    path('matchups/<int:matchup_id>/update-status/', views.update_matchup_status, name='update_matchup_status'),
    path('matchups/<int:matchup_id>/complete-step/<int:step_number>/', views.complete_matchup_step_from_detail, name='complete_matchup_step_from_detail'),
    
    # Teacher Game Instructions
    path('games/<int:game_id>/teacher-instructions/', views.teacher_game_instructions, name='teacher_game_instructions'),
    
    # Instruction Steps
    path('games/<int:game_id>/instructions/', views.game_instructions, name='game_instructions'),
    path('instruction-steps/<int:step_id>/', views.instruction_step_detail, name='instruction_step_detail'),
    path('instruction-steps/<int:step_id>/feedback/', views.submit_instruction_feedback, name='submit_instruction_feedback'),
    path('games/<int:game_id>/admin-instructions/', views.admin_instruction_steps, name='admin_instruction_steps'),
    path('admin/problematic-steps/', views.problematic_steps_dashboard, name='problematic_steps_dashboard'),
    
    # Note: Letter Density Game URLs have been removed
    # This functionality has been moved to the phoneme_density app
    
    # User Role Management
    path('manage-roles/', views.manage_user_roles, name='manage_user_roles'),
    
    # School Management
    path('schools/', views.school_list, name='school_list'),
    path('schools/create/', views.create_school, name='create_school'),
    path('schools/<int:school_id>/edit/', views.edit_school, name='edit_school'),
    
    # Instruction Management URLs (KEPT - needed for creating teacher/student instructions)
    path('manage-games/<int:game_id>/steps/<int:step_id>/instructions/', views.manage_step_instructions, name='manage_step_instructions'),
    path('manage-games/<int:game_id>/steps/<int:step_id>/instructions/create/', views.create_instruction, name='create_instruction'),
    path('manage-games/<int:game_id>/steps/<int:step_id>/instructions/<int:instruction_id>/edit/', views.edit_instruction, name='edit_instruction'),
    path('manage-games/<int:game_id>/steps/<int:step_id>/instructions/<int:instruction_id>/delete/', views.delete_instruction, name='delete_instruction'),
]
