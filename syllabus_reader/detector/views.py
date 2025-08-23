from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
import json

from aigames.models import GameMatchup, MatchupStepProgress, InstructionStep
from .models import TeamDetectorData, DetectorSubmission
from .constants import TOTAL_STEPS, STEP_NAMES


def check_step_access(matchup, user, requested_step_number):
    """
    Check if a user can access a specific step in a matchup.
    Returns (can_access, current_step, error_message)
    """
    # Get the user's team from the matchup
    user_team = None
    if user in matchup.team1.members.all():
        user_team = matchup.team1
    elif user in matchup.team2.members.all():
        user_team = matchup.team2
    
    if not user_team:
        return False, 1, "You are not part of this game."
    
    # Get or create team detector data
    team_data, created = TeamDetectorData.objects.get_or_create(
        matchup=matchup,
        team=user_team
    )
    
    # Check if the requested step is accessible
    if not team_data.is_step_accessible(requested_step_number):
        return False, team_data.current_step, f"You must complete previous steps before accessing Step {requested_step_number}."
    
    return True, team_data.current_step, None


@login_required
def step1(request, matchup_id):
    """Step 1: Setup & Configuration"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 1)
    if not can_access:
        messages.error(request, error_msg)
        return redirect('aigames:student_dashboard')
    
    # Get user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    
    # Get team data
    team_data, created = TeamDetectorData.objects.get_or_create(
        matchup=matchup,
        team=user_team
    )
    
    # Handle form submission
    if request.method == 'POST':
        # Process step 1 CO2 detector configuration data
        setup_data = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            'detection_mode': request.POST.get('detection_mode', ''),
            'sensitivity_threshold': request.POST.get('sensitivity', '700'),
            'monitoring_objectives': request.POST.get('target_parameters', ''),
            'configuration_type': 'co2_detector',
            'baseline_ppm': 400,
            'target_ppm': 700,
            'alert_threshold': request.POST.get('sensitivity', '700')
        }
        
        team_data.setup_data = setup_data
        team_data.save()
        
        messages.success(request, "Step 1 configuration saved successfully!")
        return redirect('detector:step1', matchup_id=matchup.id)
    
    # Get instructions for step 1 - filter by user role
    all_instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=1,
        is_active=True
    )
    
    # Filter instructions based on user role
    instructions = [instruction for instruction in all_instructions 
                   if instruction.is_visible_to_user(request.user)]
    
    context = {
        'matchup': matchup,
        'ai_game': matchup.ai_game,
        'user_team': user_team,
        'team_data': team_data,
        'total_steps': TOTAL_STEPS,
        'current_step': 1,
        'step_name': STEP_NAMES.get(1, 'Step 1'),
        'has_next_step': True,
        'next_step_accessible': team_data.is_step_accessible(2),
        'instructions': instructions,
    }
    
    return render(request, 'detector/step1.html', context)


@login_required
def step2(request, matchup_id):
    """Step 2: Data Collection"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 2)
    if not can_access:
        messages.error(request, error_msg)
        return redirect('aigames:student_dashboard')
    
    # Get user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    
    # Get team data
    team_data = get_object_or_404(TeamDetectorData, matchup=matchup, team=user_team)
    
    # Handle form submission
    if request.method == 'POST':
        # Process step 2 data here
        collection_data = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            # Add specific step 2 fields here
        }
        
        team_data.collection_data = collection_data
        team_data.save()
        
        messages.success(request, "Step 2 data collection saved successfully!")
        return redirect('detector:step2', matchup_id=matchup.id)
    
    # Get instructions for step 2 - filter by user role
    all_instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=2,
        is_active=True
    )
    
    # Filter instructions based on user role
    instructions = [instruction for instruction in all_instructions 
                   if instruction.is_visible_to_user(request.user)]
    
    context = {
        'matchup': matchup,
        'ai_game': matchup.ai_game,
        'user_team': user_team,
        'team_data': team_data,
        'total_steps': TOTAL_STEPS,
        'current_step': 2,
        'step_name': STEP_NAMES.get(2, 'Step 2'),
        'has_previous_step': True,
        'has_next_step': True,
        'next_step_accessible': team_data.is_step_accessible(3),
        'instructions': instructions,
    }
    
    return render(request, 'detector/step2.html', context)


@login_required
def step3(request, matchup_id):
    """Step 3: Analysis & Detection"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 3)
    if not can_access:
        messages.error(request, error_msg)
        return redirect('aigames:student_dashboard')
    
    # Get user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    
    # Get team data
    team_data = get_object_or_404(TeamDetectorData, matchup=matchup, team=user_team)
    
    # Handle form submission
    if request.method == 'POST':
        # Process step 3 data here
        analysis_data = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            # Add specific step 3 fields here
        }
        
        team_data.analysis_data = analysis_data
        team_data.save()
        
        messages.success(request, "Step 3 analysis saved successfully!")
        return redirect('detector:step3', matchup_id=matchup.id)
    
    # Get instructions for step 3 - filter by user role
    all_instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=3,
        is_active=True
    )
    
    # Filter instructions based on user role
    instructions = [instruction for instruction in all_instructions 
                   if instruction.is_visible_to_user(request.user)]
    
    context = {
        'matchup': matchup,
        'ai_game': matchup.ai_game,
        'user_team': user_team,
        'team_data': team_data,
        'total_steps': TOTAL_STEPS,
        'current_step': 3,
        'step_name': STEP_NAMES.get(3, 'Step 3'),
        'has_previous_step': True,
        'has_next_step': True,
        'next_step_accessible': team_data.is_step_accessible(4),
        'instructions': instructions,
    }
    
    return render(request, 'detector/step3.html', context)


@login_required
def step4(request, matchup_id):
    """Step 4: Results & Validation"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 4)
    if not can_access:
        messages.error(request, error_msg)
        return redirect('aigames:student_dashboard')
    
    # Get user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    
    # Get team data
    team_data = get_object_or_404(TeamDetectorData, matchup=matchup, team=user_team)
    
    # Handle form submission
    if request.method == 'POST':
        # Process step 4 data here
        results_data = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            # Add specific step 4 fields here
        }
        
        team_data.results_data = results_data
        team_data.save()
        
        messages.success(request, "Step 4 results saved successfully!")
        return redirect('detector:step4', matchup_id=matchup.id)
    
    # Get instructions for step 4 - filter by user role
    all_instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=4,
        is_active=True
    )
    
    # Filter instructions based on user role
    instructions = [instruction for instruction in all_instructions 
                   if instruction.is_visible_to_user(request.user)]
    
    context = {
        'matchup': matchup,
        'ai_game': matchup.ai_game,
        'user_team': user_team,
        'team_data': team_data,
        'total_steps': TOTAL_STEPS,
        'current_step': 4,
        'step_name': STEP_NAMES.get(4, 'Step 4'),
        'has_previous_step': True,
        'has_next_step': False,
        'instructions': instructions,
    }
    
    return render(request, 'detector/step4.html', context)


@login_required
@require_POST
def complete_step(request, matchup_id, step_number):
    """Mark a step as completed and advance to next step"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    
    if not user_team:
        messages.error(request, "You are not part of this game.")
        return redirect('aigames:student_dashboard')
    
    # Get team data
    team_data = get_object_or_404(TeamDetectorData, matchup=matchup, team=user_team)
    
    # Complete the step
    team_data.complete_step(step_number)
    
    messages.success(request, f"Step {step_number} completed successfully!")
    
    # Redirect to next step or current step
    if step_number < TOTAL_STEPS:
        return redirect(f'detector:step{step_number + 1}', matchup_id=matchup.id)
    else:
        return redirect(f'detector:step{step_number}', matchup_id=matchup.id)


@login_required
@require_POST
def save_step_data(request, matchup_id):
    """AJAX endpoint for saving step data without page refresh"""
    try:
        matchup = get_object_or_404(GameMatchup, id=matchup_id)
        
        # Get user's team
        user_team = None
        if request.user in matchup.team1.members.all():
            user_team = matchup.team1
        elif request.user in matchup.team2.members.all():
            user_team = matchup.team2
        
        if not user_team:
            return JsonResponse({'success': False, 'error': 'Not part of this game'})
        
        team_data = get_object_or_404(TeamDetectorData, matchup=matchup, team=user_team)
        
        # Parse the posted data
        data = json.loads(request.body)
        step_number = data.get('step_number')
        step_data = data.get('data', {})
        
        # Save to appropriate field based on step
        if step_number == 1:
            team_data.setup_data.update(step_data)
        elif step_number == 2:
            team_data.collection_data.update(step_data)
        elif step_number == 3:
            team_data.analysis_data.update(step_data)
        elif step_number == 4:
            team_data.results_data.update(step_data)
        
        team_data.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def reset_game(request, matchup_id):
    """Reset the game progress for the team"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    
    if not user_team:
        messages.error(request, "You are not part of this game.")
        return redirect('aigames:student_dashboard')
    
    # Reset team data
    try:
        team_data = TeamDetectorData.objects.get(matchup=matchup, team=user_team)
        team_data.current_step = 1
        team_data.step1_completed = False
        team_data.step2_completed = False
        team_data.step3_completed = False
        team_data.step4_completed = False
        team_data.setup_data = {}
        team_data.collection_data = {}
        team_data.analysis_data = {}
        team_data.results_data = {}
        team_data.save()
        
        # Delete any submissions
        DetectorSubmission.objects.filter(team_data=team_data).delete()
        
        messages.success(request, "Game progress has been reset successfully!")
        
    except TeamDetectorData.DoesNotExist:
        messages.info(request, "No game data to reset.")
    
    return redirect('detector:step1', matchup_id=matchup.id)
