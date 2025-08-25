from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from aigames.models import Team, GameMatchup, MatchupStepProgress
from aigames.decorators import teacher_can_view_team, get_user_team_or_viewing_team, should_allow_form_submission
from .models import TeamOverlapData, OverlapSubmission
from .constants import *


@login_required
@teacher_can_view_team
def step1(request, matchup_id):
    """Step 1: Game Setup and Configuration"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get the appropriate team (user's team or teacher's viewing team)
    user_team = get_user_team_or_viewing_team(request, matchup)
    
    # Check if this is a teacher viewing general content (non-validation step)
    is_teacher_general_view = (hasattr(request, 'is_teacher_viewing') and 
                              request.is_teacher_viewing and 
                              user_team is None)
    
    if not user_team and not is_teacher_general_view:
        messages.error(request, "You are not part of a team for this game.")
        return redirect('aigames:student_dashboard')

    # For teacher general viewing, create dummy data or use default values
    if is_teacher_general_view:
        team_data = None
        step1_completed = False
        # Show default configuration for teachers
        sensitivity_level = 50
        threshold_value = 0.75
        overlap_mode = 'standard'
    else:
        team_data, created = TeamOverlapData.objects.get_or_create(
            team=user_team, 
            matchup=matchup,
            defaults={'current_step': 1}
        )
        
        # Refresh from database to ensure we have the latest data
        team_data.refresh_from_db()
        
        # Use team's actual configuration
        sensitivity_level = team_data.sensitivity_level
        threshold_value = team_data.threshold_value
        overlap_mode = team_data.overlap_mode
    
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
        'is_teacher_viewing': hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode,
        'is_teacher_general_view': is_teacher_general_view,
        'current_sensitivity': sensitivity_level,
        'current_threshold': threshold_value,
        'current_mode': overlap_mode,
    }
    
    return render(request, 'overlap/step1.html', context)


@login_required
@teacher_can_view_team
def step2(request, matchup_id):
    """Step 2: Data Collection"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get the appropriate team (user's team or teacher's viewing team)
    user_team = get_user_team_or_viewing_team(request, matchup)
    
    # Check if this is a teacher viewing general content (non-validation step)
    is_teacher_general_view = (hasattr(request, 'is_teacher_viewing') and 
                              request.is_teacher_viewing and 
                              user_team is None)
    
    if not user_team and not is_teacher_general_view:
        messages.error(request, "You are not part of a team for this game.")
        return redirect('aigames:student_dashboard')

    # For teacher general viewing, show example data
    if is_teacher_general_view:
        team_data = None
        step2_completed = False
        instructions = []
        game_step = matchup.ai_game.get_step_by_number(2)
        if game_step:
            instructions = game_step.get_instructions_for_user(request.user)
        
        context = {
            'matchup': matchup,
            'team': None,
            'team_data': None,
            'step_name': STEP_NAMES['step2'],
            'current_step': 2,
            'total_steps': TOTAL_STEPS,
            'has_next_step': True,
            'next_step_accessible': True,  # Always allow teacher to navigate
            'instructions': instructions,
            'is_teacher_viewing': True,
            'allow_form_submission': False,
        }
        return render(request, 'overlap/step2.html', context)
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    
    # Check if step 1 is completed using MatchupStepProgress (only for students)
    step1_progress = matchup.get_progress_for_step(1)
    step1_completed = step1_progress.is_completed if step1_progress else False
    
    if not step1_completed and not hasattr(request, 'teacher_viewing_mode'):
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
        'is_teacher_viewing': hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode,
        'allow_form_submission': should_allow_form_submission(request),
    }
    
    return render(request, 'overlap/step2.html', context)


@login_required
@teacher_can_view_team
def step3(request, matchup_id):
    """Step 3: Circle Placement Challenge"""
    print(f"[DEBUG] step3 view called for matchup {matchup_id}")
    print(f"[DEBUG] User: {request.user}")
    print(f"[DEBUG] Request attributes: teacher_viewing_mode={getattr(request, 'teacher_viewing_mode', 'NOT_SET')}")
    
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get the appropriate team (user's team or teacher's viewing team)
    user_team = get_user_team_or_viewing_team(request, matchup)
    print(f"[DEBUG] user_team from helper: {user_team}")
    
    if not user_team:
        print(f"[DEBUG] No user team found - redirecting")
        messages.error(request, "You are not part of a team for this game.")
        return redirect('aigames:student_dashboard')
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    print(f"[DEBUG] team_data retrieved: {team_data}")
    print(f"[DEBUG] team_data.circle_placement_submitted: {team_data.circle_placement_submitted}")
    print(f"[DEBUG] team_data.circle_x: {team_data.circle_x}, circle_y: {team_data.circle_y}")
    
    # Check if step 2 is completed using MatchupStepProgress (only for students)
    step2_progress = matchup.get_progress_for_step(2)
    step2_completed = step2_progress.is_completed if step2_progress else False
    
    if not step2_completed and not hasattr(request, 'teacher_viewing_mode'):
        print(f"[DEBUG] Step 2 not completed - redirecting to step2")
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
    
    if request.method == 'POST' and should_allow_form_submission(request):
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
                'is_teacher_viewing': hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode,
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
        'is_teacher_viewing': hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode,
    }
    
    return render(request, 'overlap/step3.html', context)


@login_required
@teacher_can_view_team
def step4(request, matchup_id):
    """Step 4: Interactive Evaluation Canvas"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get the appropriate team (user's team or teacher's viewing team)
    user_team = get_user_team_or_viewing_team(request, matchup)
    
    if not user_team:
        messages.error(request, "You are not part of a team for this game.")
        return redirect('aigames:student_dashboard')
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    
    # Check if step 3 is completed (only for students, not teachers)
    if not hasattr(request, 'teacher_viewing_mode'):
        if not team_data.can_access_step(4):
            messages.warning(request, "You must complete previous steps first.")
            return redirect('overlap:step3', matchup_id=matchup_id)
    
    # Get opponent team and their circle data
    opponent_team = matchup.team1 if user_team == matchup.team2 else matchup.team2
    opponent_team_data = TeamOverlapData.objects.filter(team=opponent_team, matchup=matchup).first()
    
    # Get opponent's circle position from step 3
    opponent_circle_x = 200  # Default
    opponent_circle_y = 150  # Default
    if opponent_team_data and opponent_team_data.circle_x is not None:
        opponent_circle_x = opponent_team_data.circle_x
        opponent_circle_y = opponent_team_data.circle_y
    
    # Check if form submission should be allowed (not for teachers viewing)
    allow_form_submission = should_allow_form_submission(request)
    
    if request.method == 'POST' and allow_form_submission:
        # Handle click data submission (if you want to store it)
        # For now, just mark step as completed
        team_data.complete_step(4)
        messages.success(request, "Step 4 completed successfully!")
        return redirect('overlap:complete_step', matchup_id=matchup_id)
    
    # Get instructions for this step
    instructions = []
    game_step = matchup.ai_game.get_step_by_number(4)
    if game_step:
        instructions = game_step.get_instructions_for_user(request.user)
    
    context = {
        'matchup': matchup,
        'team': user_team,
        'team_data': team_data,
        'opponent_team': opponent_team,
        'step_name': STEP_NAMES['step4'],
        'current_step': 4,
        'total_steps': TOTAL_STEPS,
        'is_teacher_viewing': hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode,
        'allow_form_submission': allow_form_submission,
        'opponent_circle_x': int(opponent_circle_x),
        'opponent_circle_y': int(opponent_circle_y),
        'instructions': instructions,
        'existing_clicks': team_data.evaluation_clicks,
        'existing_click_count': team_data.click_count,
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


@login_required
@teacher_can_view_team
def save_strategy(request, matchup_id):
    """Save team's evaluation strategy for step 4"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('overlap:step4', matchup_id=matchup_id)
    
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get the appropriate team (user's team, not teacher's viewing team)
    user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
    
    if not user_team:
        messages.error(request, "You are not part of a team for this game.")
        return redirect('aigames:student_dashboard')
    
    # Don't allow teachers to save strategy when viewing
    if hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode:
        messages.error(request, "Teachers cannot save strategies while viewing team data.")
        return redirect('overlap:step4', matchup_id=matchup_id)
    
    team_data = get_object_or_404(TeamOverlapData, team=user_team, matchup=matchup)
    
    # Get strategy from form
    strategy = request.POST.get('strategy', '').strip()
    
    # Validate strategy length
    if len(strategy) > 500:
        if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded' and 'XMLHttpRequest' in request.META.get('HTTP_X_REQUESTED_WITH', ''):
            return JsonResponse({'success': False, 'error': 'Strategy cannot exceed 500 characters.'})
        messages.error(request, "Strategy cannot exceed 500 characters.")
        return redirect('overlap:step4', matchup_id=matchup_id)
    
    # Save strategy
    team_data.evaluation_strategy = strategy
    team_data.save()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/x-www-form-urlencoded' in request.headers.get('Content-Type', ''):
        return JsonResponse({'success': True})
    
    messages.success(request, "Evaluation strategy saved successfully!")
    return redirect('overlap:step4', matchup_id=matchup_id)


@login_required
@require_POST
def save_click(request, matchup_id):
    """Save a click point to the database via AJAX"""
    try:
        matchup = get_object_or_404(GameMatchup, id=matchup_id)
        
        # Get the appropriate team (user's team, not teacher's viewing team)
        user_team = Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or \
                    Team.objects.filter(members=request.user, matchups_as_team2=matchup).first()
        
        if not user_team:
            return JsonResponse({'success': False, 'error': 'You are not part of a team for this game.'})
        
        # Don't allow teachers to save clicks when viewing
        if hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode:
            return JsonResponse({'success': False, 'error': 'Teachers cannot save clicks while viewing team data.'})
        
        team_data, created = TeamOverlapData.objects.get_or_create(
            team=user_team,
            matchup=matchup
        )
        
        # Get click data from request
        x = float(request.POST.get('x'))
        y = float(request.POST.get('y'))
        
        # Initialize clicks list if None
        if team_data.evaluation_clicks is None:
            team_data.evaluation_clicks = []
        
        # Add new click (limit to 12)
        if len(team_data.evaluation_clicks) < 12:
            team_data.evaluation_clicks.append({'x': x, 'y': y})
            team_data.click_count = len(team_data.evaluation_clicks)
            team_data.save()
        
        return JsonResponse({
            'success': True, 
            'click_count': team_data.click_count,
            'total_clicks': len(team_data.evaluation_clicks)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
