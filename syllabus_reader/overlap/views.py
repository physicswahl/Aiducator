from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from aigames.models import Team, GameMatchup, MatchupStepProgress
from .models import TeamOverlapData, OverlapSubmission
from .constants import *


@login_required
def step1(request, matchup_id):
    """Step 1: Game Setup and Configuration"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check if teacher is viewing a specific team's work
    teacher_viewing_team_id = request.GET.get('team')
    if teacher_viewing_team_id:
        # Verify user is a teacher for this game's school
        if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'teacher':
            user_team = get_object_or_404(Team, id=teacher_viewing_team_id)
            # Verify this team is part of the matchup
            if user_team != matchup.team1 and user_team != matchup.team2:
                messages.error(request, "Invalid team access.")
                return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
        else:
            messages.error(request, "You don't have permission to view team data.")
            return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    else:
        # Regular student access - find their team
        user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                    Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
        if not user_team:
            messages.error(request, "You are not part of a team for this game.")
            return redirect('aigames:student_dashboard')
    
    team_data, created = TeamOverlapData.objects.get_or_create(
        team=user_team, 
        matchup=matchup,
        defaults={'current_step': 1}
    )
    
    # Refresh from database to ensure we have the latest data
    team_data.refresh_from_db()
    
    # Check if step 1 is completed using MatchupStepProgress
    step1_progress = matchup.get_progress_for_step(1)
    step1_completed = step1_progress.is_completed if step1_progress else False
    
    # Get instructions for this step
    instructions = []
    game_step = matchup.ai_game.get_step_by_number(1)
    if game_step:
        instructions = game_step.get_instructions_for_user(request.user)
    
    context = {
        'matchup': matchup,
        'team': user_team,
        'team_data': team_data,
        'step_name': STEP_NAMES['step1'],
        'current_step': 1,
        'total_steps': TOTAL_STEPS,
        'has_next_step': True,
        'next_step_accessible': step1_completed,
        'sensitivity_levels': range(1, 101),
        'threshold_options': [i/100 for i in range(50, 101, 5)],
        'mode_options': ['standard', 'enhanced', 'advanced'],
        'instructions': instructions,
        'is_teacher_viewing': bool(teacher_viewing_team_id),
    }
    
    return render(request, 'overlap/step1.html', context)


@login_required
def step2(request, matchup_id):
    """Step 2: Data Collection"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check if teacher is viewing a specific team's work
    teacher_viewing_team_id = request.GET.get('team')
    if teacher_viewing_team_id:
        # Verify user is a teacher for this game's school
        if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'teacher':
            user_team = get_object_or_404(Team, id=teacher_viewing_team_id)
            # Verify this team is part of the matchup
            if user_team != matchup.team1 and user_team != matchup.team2:
                messages.error(request, "Invalid team access.")
                return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
        else:
            messages.error(request, "You don't have permission to view team data.")
            return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    else:
        # Regular student access - find their team
        user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                    Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
        if not user_team:
            messages.error(request, "You are not part of a team for this game.")
            return redirect('aigames:student_dashboard')
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    
    # Check if step 1 is completed using MatchupStepProgress (only for students)
    step1_progress = matchup.get_progress_for_step(1)
    step1_completed = step1_progress.is_completed if step1_progress else False
    
    if not step1_completed and not teacher_viewing_team_id:
        messages.warning(request, "You must complete Step 1 first.")
        return redirect('overlap:step1', matchup_id=matchup_id)
    
    # Check if step 2 is completed using MatchupStepProgress
    step2_progress = matchup.get_progress_for_step(2)
    step2_completed = step2_progress.is_completed if step2_progress else False
    
    # Get instructions for this step
    instructions = []
    game_step = matchup.ai_game.get_step_by_number(2)
    if game_step:
        instructions = game_step.get_instructions_for_user(request.user)
    
    context = {
        'matchup': matchup,
        'team': user_team,
        'team_data': team_data,
        'step_name': STEP_NAMES['step2'],
        'current_step': 2,
        'total_steps': TOTAL_STEPS,
        'has_next_step': True,
        'next_step_accessible': step2_completed,
        'instructions': instructions,
        'is_teacher_viewing': bool(teacher_viewing_team_id),
    }
    
    return render(request, 'overlap/step2.html', context)


@login_required
def step3(request, matchup_id):
    """Step 3: Circle Placement Challenge"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check if teacher is viewing a specific team's work
    teacher_viewing_team_id = request.GET.get('team')
    if teacher_viewing_team_id:
        # Verify user is a teacher for this game's school
        if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'teacher':
            user_team = get_object_or_404(Team, id=teacher_viewing_team_id)
            # Verify this team is part of the matchup
            if user_team != matchup.team1 and user_team != matchup.team2:
                messages.error(request, "Invalid team access.")
                return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
        else:
            messages.error(request, "You don't have permission to view team data.")
            return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    else:
        # Regular student access - find their team
        user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                    Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
        if not user_team:
            messages.error(request, "You are not part of a team for this game.")
            return redirect('aigames:student_dashboard')
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    
    # Check if step 2 is completed using MatchupStepProgress (only for students)
    step2_progress = matchup.get_progress_for_step(2)
    step2_completed = step2_progress.is_completed if step2_progress else False
    
    if not step2_completed and not teacher_viewing_team_id:
        messages.warning(request, "You must complete Step 2 before accessing Step 3.")
        return redirect('overlap:step2', matchup_id=matchup_id)
    
    # Check step 3 completion status - requires both teams to submit and be validated
    step3_progress = matchup.get_progress_for_step(3)
    step3_completed = step3_progress.is_completed if step3_progress else False
    
    # Get both teams' data to check if both have submitted and been validated
    other_team = matchup.get_other_team(user_team)
    other_team_data = None
    if other_team:
        other_team_data, _ = TeamOverlapData.objects.get_or_create(
            team=other_team, 
            matchup=matchup,
            defaults={'current_step': 1}
        )
    
    # Check if current team can proceed to next step
    # Requires: 1) Current team submitted and validated, 2) Other team submitted and validated
    current_team_ready = (team_data.circle_placement_submitted and step3_completed)
    other_team_ready = (other_team_data and 
                       other_team_data.circle_placement_submitted and 
                       step3_completed)  # step3_completed means teacher validated for the matchup
    
    next_step_accessible = current_team_ready and other_team_ready
    
    if request.method == 'POST' and not teacher_viewing_team_id:
        # Handle circle placement submission (only for students, not teachers viewing)
        circle_x = float(request.POST.get('circle_x', 0))
        circle_y = float(request.POST.get('circle_y', 0))
        placement_notes = request.POST.get('placement_notes', '')
        
        # Validate circle is fully on canvas (assuming 400x300 canvas with radius 40)
        canvas_width = 400
        canvas_height = 300
        circle_radius = 40
        
        if (circle_x < circle_radius or circle_x > canvas_width - circle_radius or 
            circle_y < circle_radius or circle_y > canvas_height - circle_radius):
            messages.error(request, "Circle must be fully within the canvas boundaries!")
            
            # Get instructions for error case too
            instructions = []
            game_step = matchup.ai_game.get_step_by_number(3)
            if game_step:
                instructions = game_step.get_instructions_for_user(request.user)
            
            return render(request, 'overlap/step3.html', {
                'matchup': matchup,
                'team': user_team,
                'team_data': team_data,
                'other_team': other_team,
                'other_team_data': other_team_data,
                'step_name': STEP_NAMES['step3'],
                'current_step': 3,
                'total_steps': TOTAL_STEPS,
                'has_next_step': True,
                'next_step_accessible': next_step_accessible,
                'step3_completed': step3_completed,
                'current_team_ready': current_team_ready,
                'other_team_ready': other_team_ready,
                'instructions': instructions,
                'error_message': "Circle must be fully within the canvas boundaries!",
                'is_teacher_viewing': bool(teacher_viewing_team_id),
            })
        
        team_data.circle_x = circle_x
        team_data.circle_y = circle_y
        team_data.placement_notes = placement_notes
        team_data.circle_placement_submitted = True
        team_data.save()
        
        messages.success(request, "Circle placement submitted successfully! Waiting for teacher validation.")
        return redirect('overlap:step3', matchup_id=matchup_id)
    
    # Get instructions for this step
    instructions = []
    game_step = matchup.ai_game.get_step_by_number(3)
    if game_step:
        instructions = game_step.get_instructions_for_user(request.user)
    
    context = {
        'matchup': matchup,
        'team': user_team,
        'team_data': team_data,
        'other_team': other_team,
        'other_team_data': other_team_data,
        'step_name': STEP_NAMES['step3'],
        'current_step': 3,
        'total_steps': TOTAL_STEPS,
        'has_next_step': True,
        'next_step_accessible': next_step_accessible,
        'step3_completed': step3_completed,
        'current_team_ready': current_team_ready,
        'other_team_ready': other_team_ready,
        'instructions': instructions,
        'is_teacher_viewing': bool(teacher_viewing_team_id),
    }
    
    return render(request, 'overlap/step3.html', context)


@login_required
def step4(request, matchup_id):
    """Step 4: Final Results and Conclusions"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
    if not user_team:
        messages.error(request, "You are not part of a team for this game.")
        return redirect('aigames:student_dashboard')
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    
    if not team_data.can_access_step(4):
        messages.warning(request, "You must complete previous steps first.")
        return redirect('overlap:step3', matchup_id=matchup_id)
    
    if request.method == 'POST':
        # Handle final submission
        final_score = float(request.POST.get('final_score', 0))
        conclusions = request.POST.get('conclusions', '')
        
        team_data.final_score = final_score
        team_data.conclusions = conclusions
        team_data.completed_at = timezone.now()
        team_data.complete_step(4)
        
        return redirect('overlap:complete_step', matchup_id=matchup_id)
    
    context = {
        'matchup': matchup,
        'team': user_team,
        'team_data': team_data,
        'step_name': STEP_NAMES['step4'],
        'current_step': 4,
        'total_steps': TOTAL_STEPS,
    }
    
    return render(request, 'overlap/step4.html', context)


@login_required
def complete_step(request, matchup_id):
    """Game completion page"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
    if not user_team:
        messages.error(request, "You are not part of a team for this game.")
        return redirect('aigames:student_dashboard')
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    
    context = {
        'matchup': matchup,
        'team': user_team,
        'team_data': team_data,
        'completion_percentage': team_data.get_completion_percentage(),
    }
    
    return render(request, 'overlap/complete.html', context)


@login_required
def reset_game(request, matchup_id):
    """Reset game progress"""
    if request.method == 'POST':
        matchup = get_object_or_404(GameMatchup, id=matchup_id)
        user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                    Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
        
        if user_team:
            try:
                team_data = TeamOverlapData.objects.get(team=user_team, matchup=matchup)
                team_data.delete()
                messages.success(request, "Game progress has been reset.")
            except TeamOverlapData.DoesNotExist:
                pass
        
        return redirect('overlap:step1', matchup_id=matchup_id)
    
    return redirect('overlap:step1', matchup_id=matchup_id)


@login_required
@csrf_exempt
def save_data(request, matchup_id):
    """AJAX endpoint for saving game data"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            matchup = get_object_or_404(GameMatchup, id=matchup_id)
            user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                        Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
            
            if not user_team:
                return JsonResponse({'success': False, 'error': 'Team not found'})
            
            team_data, created = TeamOverlapData.objects.get_or_create(
                team=user_team, 
                matchup=matchup
            )
            
            # Update fields based on data
            for key, value in data.items():
                if hasattr(team_data, key):
                    setattr(team_data, key, value)
            
            team_data.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
