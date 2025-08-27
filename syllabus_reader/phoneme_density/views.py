from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from django.db import transaction
import json
import math

from aigames.models import GameMatchup, MatchupStepProgress, InstructionStep
from .models import TeamStep4Data, TeamText, PhonemeGuess, TextGuess
from .constants import PHONEME_CHOICES, ENGLISH_PHONEME_FREQUENCIES, get_phoneme_codes

def redirect_to_step(matchup, step_number):
    """Helper function to dynamically redirect to a step using GameStep model"""
    try:
        game_step = matchup.ai_game.steps.get(step_number=step_number)
        step_url = game_step.get_url(matchup.id)
        if step_url:
            return redirect(step_url)
    except:
        pass
    # Fallback to student dashboard if step can't be found
    return redirect('aigames:student_dashboard')


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
    else:
        # User is not part of this matchup, check if they're a teacher
        if user.profile.can_create_teams:
            return True, None, None  # Teachers can access any step
        else:
            return False, None, "You are not part of this game."
    
    # Check step progress for this matchup (not team-specific)
    completed_steps = []
    matchup_progress = MatchupStepProgress.objects.filter(matchup=matchup)
    
    for progress in matchup_progress:
        step_num = progress.game_step.step_number
        if progress.completed_at is not None:
            completed_steps.append(step_num)
    
    if completed_steps:
        last_completed_step = max(completed_steps)
        current_step_number = last_completed_step + 1
    else:
        current_step_number = 1  # Start with step 1 if none completed
    
    # Students can access the current step or any previous completed step
    if requested_step_number <= current_step_number:
        return True, None, None
    else:
        return False, current_step_number, f"Complete Step {current_step_number} before accessing Step {requested_step_number}."


# Matchup-based views (new architecture)
@login_required
def step1(request, matchup_id):
    """Step 1: Text analysis - Display instructions and four texts (matchup-based)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 1)
    if not can_access:
        messages.error(request, error_msg)
        return redirect('aigames:student_dashboard')
    
    # Create or get progress record for this matchup and step
    game_step = matchup.ai_game.steps.get(step_number=1)
    progress, created = MatchupStepProgress.objects.get_or_create(
        matchup=matchup,
        game_step=game_step,
        defaults={'started_at': timezone.now()}
    )
    
    # Get instructions for step 1
    instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=1
    )
    
    # Sample texts for phoneme density analysis
    texts = [
        {
            'id': 1,
            'title': 'Text 1',
            'content': 'The red roses grew rapidly in the garden. Robert ran around the rusty railroad tracks.',
        },
        {
            'id': 2,
            'title': 'Text 2', 
            'content': 'The beautiful blue sky stretched endlessly above the peaceful meadow.',
        },
        {
            'id': 3,
            'title': 'Text 3',
            'content': 'Students studied silently in the spacious library during the summer session.',
        },
        {
            'id': 4,
            'title': 'Text 4',
            'content': 'Bright orange carrots and crisp green broccoli were arranged in colorful rows.',
        }
    ]
    
    # Get the AI game for context
    ai_game = matchup.ai_game
    
    # Get total steps for this game
    total_steps = ai_game.steps.filter(is_active=True).count()
    
    # Check if there are more steps and if next step is accessible
    has_next_step = total_steps > 1
    next_step_accessible = False
    if has_next_step:
        # Check if step 1 is complete to allow access to step 2
        step1_progress = matchup.get_progress_for_step(1)
        next_step_accessible = step1_progress and step1_progress.is_completed
    
    context = {
        'matchup': matchup,
        'ai_game': ai_game,
        'instructions': instructions,
        'texts': texts,
        'step_number': 1,
        'step_title': 'Text Analysis',
        'total_steps': total_steps,
        'current_step': 1,
        'step_name': 'Step 1: Text Analysis',
        'has_next_step': has_next_step,
        'next_step_accessible': next_step_accessible,
        # Variables for gamepage template footer navigation
        'next_step_url': reverse('phoneme_density:step2', kwargs={'matchup_id': matchup.id}) if has_next_step else None,
    }
    
    return render(request, 'phoneme_density/step1.html', context)


@login_required
def step2(request, matchup_id):
    """Step 2: Show text labels - reveal which texts are phoneme-heavy (matchup-based)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 2)
    if not can_access:
        messages.error(request, error_msg)
        if current_step:
            return redirect_to_step(matchup, current_step)
        return redirect('aigames:student_dashboard')
    
    # Get instructions for step 2
    instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=2
    )
    
    # Same texts as step 1, but now with labels revealed
    texts = [
        {
            'id': 1,
            'title': 'Text 1',
            'content': 'The red roses grew rapidly in the garden. Robert ran around the rusty railroad tracks.',
            'is_phoneme_heavy': True
        },
        {
            'id': 2,
            'title': 'Text 2', 
            'content': 'The beautiful blue sky stretched endlessly above the peaceful meadow.',
            'is_phoneme_heavy': False
        },
        {
            'id': 3,
            'title': 'Text 3',
            'content': 'Students studied silently in the spacious library during the summer session.',
            'is_phoneme_heavy': False
        },
        {
            'id': 4,
            'title': 'Text 4',
            'content': 'Bright orange carrots and crisp green broccoli were arranged in colorful rows.',
            'is_phoneme_heavy': True
        }
    ]
    
    # Get the AI game for context
    ai_game = matchup.ai_game
    
    # Get total steps for this game
    total_steps = ai_game.steps.filter(is_active=True).count()
    
    # Check if there are more steps and if next step is accessible
    has_next_step = total_steps > 2
    next_step_accessible = False
    if has_next_step:
        # Check if step 2 is complete to allow access to step 3
        step2_progress = matchup.get_progress_for_step(2)
        next_step_accessible = step2_progress and step2_progress.is_completed
    
    context = {
        'matchup': matchup,
        'ai_game': ai_game,
        'instructions': instructions,
        'texts': texts,
        'step_number': 2,
        'step_title': 'Label Reveal',
        'total_steps': total_steps,
        'current_step': 2,
        'step_name': 'Step 2: Label Reveal',
        'has_next_step': has_next_step,
        'next_step_accessible': next_step_accessible,
        # Variables for gamepage template footer navigation
        'next_step_url': reverse('phoneme_density:step3', kwargs={'matchup_id': matchup.id}) if has_next_step else None,
        'previous_step_url': reverse('phoneme_density:step1', kwargs={'matchup_id': matchup.id}),
    }
    
    return render(request, 'phoneme_density/step2.html', context)


@login_required
def step3(request, matchup_id):
    """Step 3: Show the phoneme rule - reveal the specific rule being studied (matchup-based)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 3)
    if not can_access:
        messages.error(request, error_msg)
        if current_step:
            return redirect_to_step(matchup, current_step)
        return redirect('aigames:student_dashboard')
    
    # Get instructions for step 3
    instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=3
    )
    
    # Same texts with rule highlighting
    texts = [
        {
            'id': 1,
            'title': 'Text 1',
            'content': 'The red roses grew rapidly in the garden. Robert ran around the rusty railroad tracks.',
            'is_phoneme_heavy': True
        },
        {
            'id': 2,
            'title': 'Text 2', 
            'content': 'The beautiful blue sky stretched endlessly above the peaceful meadow.',
            'is_phoneme_heavy': False
        },
        {
            'id': 3,
            'title': 'Text 3',
            'content': 'Students studied silently in the spacious library during the summer session.',
            'is_phoneme_heavy': False
        },
        {
            'id': 4,
            'title': 'Text 4',
            'content': 'Bright orange carrots and crisp green broccoli were arranged in colorful rows.',
            'is_phoneme_heavy': True
        }
    ]
    
    # Get the AI game for context
    ai_game = matchup.ai_game
    
    # Get total steps for this game
    total_steps = ai_game.steps.filter(is_active=True).count()
    
    # Check if there are more steps and if next step is accessible
    has_next_step = total_steps > 3
    next_step_accessible = False
    if has_next_step:
        # Check if step 3 is complete to allow access to step 4
        step3_progress = matchup.get_progress_for_step(3)
        next_step_accessible = step3_progress and step3_progress.is_completed
    
    context = {
        'matchup': matchup,
        'ai_game': ai_game,
        'instructions': instructions,
        'texts': texts,
        'step_number': 3,
        'step_title': 'Rule Reveal',
        'target_phoneme': 'r',  # This would come from the game configuration
        'total_steps': total_steps,
        'has_next_step': has_next_step,
        'next_step_accessible': next_step_accessible,
        
        # Variables for gamepage template
        'step_name': 'Step 3: Rule Application',
        'current_step': 3,
        'previous_step_url': reverse('phoneme_density:step2', kwargs={'matchup_id': matchup_id}),
        'next_step_url': reverse('phoneme_density:step4', kwargs={'matchup_id': matchup_id}) if has_next_step else None,
    }
    
    return render(request, 'phoneme_density/step3.html', context)


@login_required
def step4(request, matchup_id):
    """Step 4: Text generation - Teams create their own texts (matchup-based)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 4)
    if not can_access:
        messages.error(request, error_msg)
        if current_step:
            return redirect_to_step(matchup, current_step)
        return redirect('aigames:student_dashboard')
    
    # Determine user's team
    user_team = None
    is_teacher = request.user.profile.can_create_teams
    
    if not is_teacher:
        if request.user in matchup.team1.members.all():
            user_team = matchup.team1
        elif request.user in matchup.team2.members.all():
            user_team = matchup.team2
        else:
            messages.error(request, "You are not part of this game.")
            return redirect('aigames:student_dashboard')
    
    # For teachers viewing the page, show both teams or allow team selection
    if is_teacher:
        # For now, let teachers view team1's data, but this could be enhanced
        user_team = matchup.team1
    
    # Get or create step4 data for the team
    step4_data, created = TeamStep4Data.objects.get_or_create(
        matchup=matchup,
        team=user_team
    )
    
    # Handle form submission
    if request.method == 'POST':
        if request.POST.get('auto_save'):
            # Handle auto-save via AJAX
            return handle_step4_autosave(request, step4_data)
        
        # Handle regular form submission
        selected_phoneme = request.POST.get('selected_phoneme', '').strip()
        if selected_phoneme:
            step4_data.selected_phoneme = selected_phoneme
            step4_data.save()
        
        # Save all text data
        with transaction.atomic():
            for i in range(1, 9):  # Text 1-8
                text_content = request.POST.get(f'text_{i}', '').strip()
                
                # Get or create the text object
                team_text, created = TeamText.objects.get_or_create(
                    step4_data=step4_data,
                    text_number=i
                )
                
                # Only update if content changed and text isn't approved
                if team_text.content != text_content and team_text.approval_status != 'approved':
                    team_text.content = text_content
                    # Reset approval status if content changed
                    if team_text.approval_status == 'approved' and text_content != team_text.content:
                        team_text.approval_status = 'pending'
                        team_text.reviewed_by = None
                        team_text.reviewed_at = None
                        team_text.teacher_feedback = ''
                    team_text.save()
        
        # Handle submit for review
        if request.POST.get('submit_for_review'):
            # Update all non-empty texts to pending status
            for team_text in step4_data.texts.filter(content__isnull=False).exclude(content=''):
                if team_text.approval_status != 'approved':
                    team_text.approval_status = 'pending'
                    team_text.save()
            
            messages.success(request, "Your texts have been submitted for teacher review.")
        
        return redirect('phoneme_density:step4', matchup_id=matchup.id)
    
    # Prepare data for template
    text_data = []
    for i in range(1, 9):
        try:
            team_text = step4_data.texts.get(text_number=i)
            text_data.append({
                'content': team_text.content,
                'approval_status': team_text.approval_status,
                'teacher_feedback': team_text.teacher_feedback,
                'phoneme_count': team_text.phoneme_count,
                'phoneme_density': team_text.phoneme_density,
                'density_category': team_text.get_density_category(),
            })
        except TeamText.DoesNotExist:
            text_data.append({
                'content': '',
                'approval_status': None,
                'teacher_feedback': '',
                'phoneme_count': 0,
                'phoneme_density': 0.0,
                'density_category': 'low',
            })
    
    # Check if all texts are approved
    all_approved = step4_data.texts.filter(
        content__isnull=False
    ).exclude(content='').count() > 0 and step4_data.texts.filter(
        content__isnull=False
    ).exclude(content='').exclude(approval_status='approved').count() == 0
    
    # Check if user can submit (has at least one text with content)
    can_submit = step4_data.texts.filter(
        content__isnull=False
    ).exclude(content='').count() > 0
    
    # Get instructions for step 4
    instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=4
    )
    
    # Navigation context for gamepage template
    ai_game = matchup.ai_game
    total_steps = ai_game.steps.count()
    has_next_step = 4 < total_steps
    
    # Check if step 4 is complete to allow access to step 5
    step4_progress = matchup.get_progress_for_step(4)
    next_step_accessible = all_approved  # Step 4 is complete when all texts are approved

    context = {
        'matchup': matchup,
        'ai_game': ai_game,
        'step4_data': step4_data,
        'text_data': text_data,
        'selected_phoneme': step4_data.selected_phoneme,
        'phoneme_choices': PHONEME_CHOICES,
        'user_team': user_team,
        'is_teacher': is_teacher,
        'all_approved': all_approved,
        'can_submit': can_submit,
        'instructions': instructions,
        # Navigation context for gamepage template
        'step_number': 4,
        'step_title': 'Create Your Texts',
        'total_steps': total_steps,
        'current_step': 4,
        'step_name': 'Step 4: Create Your Texts',
        'has_next_step': has_next_step,
        'next_step_accessible': next_step_accessible,
        'previous_step_url': reverse('phoneme_density:step3', kwargs={'matchup_id': matchup.id}),
        'next_step_url': reverse('phoneme_density:step5', kwargs={'matchup_id': matchup.id}) if has_next_step else None,
    }
    
    return render(request, 'phoneme_density/step4.html', context)


def handle_step4_autosave(request, step4_data):
    """Handle auto-save functionality for step 4"""
    try:
        # Update selected phoneme
        selected_phoneme = request.POST.get('selected_phoneme', '').strip()
        if selected_phoneme:
            step4_data.selected_phoneme = selected_phoneme
            step4_data.save()
        
        # Save text data
        with transaction.atomic():
            for i in range(1, 9):
                text_content = request.POST.get(f'text_{i}', '').strip()
                
                team_text, created = TeamText.objects.get_or_create(
                    step4_data=step4_data,
                    text_number=i
                )
                
                # Only update if content changed and not approved
                if team_text.approval_status != 'approved':
                    team_text.content = text_content
                    team_text.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def step5(request, matchup_id):
    """Step 5: Classification competition - Teams classify each other's texts (matchup-based)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 5)
    if not can_access:
        messages.error(request, error_msg)
        if current_step:
            return redirect_to_step(matchup, current_step)
        return redirect('aigames:student_dashboard')
    
    # Get the user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
        opposing_team = matchup.team2
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
        opposing_team = matchup.team1
    else:
        # Teachers can view both teams
        user_team = matchup.team1  # Default for teachers
        opposing_team = matchup.team2
    
    # Get opponent's step 4 data and texts
    try:
        opponent_step4_data = TeamStep4Data.objects.get(matchup=matchup, team=opposing_team)
        opponent_texts = opponent_step4_data.texts.all().order_by('text_number')
    except TeamStep4Data.DoesNotExist:
        messages.error(request, f"{opposing_team.name} hasn't completed Step 4 yet.")
        return redirect_to_step(matchup, 4)
    
    # Get or create phoneme guess for this team
    phoneme_guess, created = PhonemeGuess.objects.get_or_create(
        matchup=matchup,
        guessing_team=user_team,
        target_team=opposing_team
    )
    
    # Handle form submission
    if request.method == 'POST':
        if 'submit_guesses' in request.POST:
            try:
                with transaction.atomic():
                    # Update phoneme guess
                    phoneme_guess.phoneme_guess = request.POST.get('phoneme_guess', '')
                    phoneme_guess.rule_description = request.POST.get('rule_description', '')
                    phoneme_guess.save()
                    
                    # Clear existing text guesses
                    phoneme_guess.text_guesses.all().delete()
                    
                    # Create new text guesses
                    for i in range(1, 9):  # 8 texts
                        follows_rule = request.POST.get(f'text_{i}_follows_rule') == 'on'
                        TextGuess.objects.create(
                            phoneme_guess=phoneme_guess,
                            text_number=i,
                            follows_rule=follows_rule
                        )
                    
                    messages.success(request, "Your guesses have been submitted successfully!")
                    return redirect('phoneme_density:step5', matchup_id=matchup_id)
                    
            except Exception as e:
                messages.error(request, f"Error saving guesses: {str(e)}")
    
    # Get existing text guesses for display
    existing_text_guesses = {}
    for text_guess in phoneme_guess.text_guesses.all():
        existing_text_guesses[text_guess.text_number] = text_guess.follows_rule
    
    # Get instructions for this step
    instructions = InstructionStep.objects.filter(
        game_step__ai_game=matchup.ai_game,
        game_step__step_number=5
    ).order_by('order')
    
    # Check if guesses have been submitted
    guesses_submitted = (
        phoneme_guess.phoneme_guess and 
        phoneme_guess.text_guesses.exists()
    )
    
    context = {
        'matchup': matchup,
        'team': user_team,
        'opposing_team': opposing_team,
        'opponent_texts': opponent_texts,
        'phoneme_guess': phoneme_guess.phoneme_guess,
        'rule_description': phoneme_guess.rule_description,
        'selected_texts': [k for k, v in existing_text_guesses.items() if v],
        'phoneme_choices': PHONEME_CHOICES,
        'instructions': instructions,
        'guesses_submitted': guesses_submitted,
    }
    
    return render(request, 'phoneme_density/step5.html', context)


@login_required
def step6(request, matchup_id):
    """Step 6: ML analysis results - Show how ML performed (matchup-based)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 6)
    if not can_access:
        messages.error(request, error_msg)
        return redirect('aigames:student_dashboard')
    
    # TODO: Implement step 6 functionality
    messages.info(request, "Step 6 is not yet implemented.")
    return redirect_to_step(matchup, 3)


@login_required
def complete_matchup_step(request, matchup_id, step_number):
    """Mark a step as completed for the current user's team (teacher function)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Only teachers can mark steps as complete
    if not request.user.profile.can_create_teams:
        messages.error(request, "Only teachers can mark steps as complete.")
        return redirect('aigames:student_dashboard')
    
    # Get the game step
    try:
        game_step = matchup.ai_game.steps.get(step_number=step_number)
    except:
        messages.error(request, f"Step {step_number} not found.")
        return redirect('aigames:student_dashboard')
    
    # Get the game step
    game_step = matchup.ai_game.steps.get(step_number=step_number)
    
    # Mark step as complete for the matchup
    progress, created = MatchupStepProgress.objects.get_or_create(
        matchup=matchup,
        game_step=game_step,
        defaults={'started_at': timezone.now()}
    )
    if not progress.completed_at:
        progress.completed_at = timezone.now()
        progress.is_completed = True
        progress.save()

    messages.success(request, f"Step {step_number} marked as complete.")
    return redirect_to_step(matchup, 1)


@login_required
def mark_step_complete(request, matchup_id, step_number):
    """Simple view to mark a step as complete (for testing)"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get the game step
    game_step = matchup.ai_game.steps.get(step_number=step_number)
    
    # Mark step as complete for the matchup
    progress, created = MatchupStepProgress.objects.get_or_create(
        matchup=matchup,
        game_step=game_step,
        defaults={'started_at': timezone.now()}
    )
    if not progress.completed_at:
        progress.completed_at = timezone.now()
        progress.is_completed = True
        progress.save()
        messages.success(request, f"Step {step_number} marked as complete!")
    else:
        messages.info(request, f"Step {step_number} was already complete.")
    
    return redirect_to_step(matchup, step_number)


@login_required 
def export_step1_pdf(request, matchup_id):
    """Export Step 1 analysis as PDF"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Check access
    can_access, current_step, error_msg = check_step_access(matchup, request.user, 1)
    if not can_access:
        messages.error(request, error_msg)
        return redirect('aigames:student_dashboard')
    
    # Sample texts for the PDF
    texts = [
        {
            'id': 1,
            'title': 'Text 1',
            'content': 'The red roses grew rapidly in the garden. Robert ran around the rusty railroad tracks.',
        },
        {
            'id': 2,
            'title': 'Text 2', 
            'content': 'The beautiful blue sky stretched endlessly above the peaceful meadow.',
        },
        {
            'id': 3,
            'title': 'Text 3',
            'content': 'Students studied silently in the spacious library during the summer session.',
        },
        {
            'id': 4,
            'title': 'Text 4',
            'content': 'Bright orange carrots and crisp green broccoli were arranged in colorful rows.',
        }
    ]
    
    context = {
        'matchup': matchup,
        'texts': texts,
        'step_number': 1,
        'step_title': 'Text Analysis'
    }
    
    template = get_template('phoneme_density/step1_pdf_template.html')
    html = template.render(context)
    
    response = HttpResponse(html, content_type='text/html')
    response['Content-Disposition'] = f'inline; filename="step1_analysis_matchup_{matchup_id}.html"'
    
    return response


def calculate_phoneme_frequency(text, phoneme):
    """Calculate phoneme frequency using the same logic as step 4"""
    text_lower = text.lower()
    phoneme_count = 0
    
    # Handle different phoneme patterns (same logic as step 4 JavaScript)
    if phoneme == 'f':
        phoneme_count = (len([m for m in text_lower if m == 'f']) + 
                        text_lower.count('ph') + 
                        text_lower.count('gh'))
    elif phoneme == 'k':
        import re
        phoneme_count = (len([m for m in text_lower if m == 'k']) + 
                        text_lower.count('ck') + 
                        len(re.findall(r'c(?=[aiou])', text_lower)) + 
                        text_lower.count('qu'))
    elif phoneme == 'sh':
        import re
        phoneme_count = (text_lower.count('sh') + 
                        len(re.findall(r'ti(?=on)', text_lower)) + 
                        len(re.findall(r'ci(?=al|an)', text_lower)) + 
                        len(re.findall(r'si(?=on)', text_lower)) + 
                        len(re.findall(r'ch(?=ef|ai)', text_lower)))
    elif phoneme == 'ch':
        import re
        phoneme_count = (text_lower.count('ch') + 
                        text_lower.count('tch') + 
                        len(re.findall(r'tu(?=re)', text_lower)))
    elif phoneme == 'j':
        import re
        phoneme_count = (len([m for m in text_lower if m == 'j']) + 
                        text_lower.count('dge') + 
                        len(re.findall(r'g(?=[ei])', text_lower)))
    elif phoneme in ['th', 'dh']:
        phoneme_count = text_lower.count('th')
    elif phoneme == 'zh':
        import re
        phoneme_count = (len(re.findall(r'ge(?=$|[^aeiou])', text_lower)) + 
                        len(re.findall(r'si(?=on)', text_lower)) + 
                        len(re.findall(r's(?=ure|ion)', text_lower)))
    elif phoneme == 'ng':
        import re
        phoneme_count = (text_lower.count('ng') + 
                        len(re.findall(r'n(?=[kg])', text_lower)))
    elif phoneme == 'z':
        import re
        phoneme_count = (len([m for m in text_lower if m == 'z']) + 
                        len(re.findall(r's(?=[^aeiou]|$)', text_lower)))
    else:
        # Simple single-character phonemes
        phoneme_count = len([m for m in text_lower if m == phoneme])
    
    total_chars = len(text_lower.replace(' ', ''))  # Characters without spaces
    return (phoneme_count / total_chars * 100) if total_chars > 0 else 0


@login_required
def text_analysis(request, matchup_id, text_number):
    """Display phoneme frequency spider graph for a specific text"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    # Get the user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    else:
        # Teachers can view any team's data
        user_team = matchup.team1  # Default for teachers
    
    # Get the team's step 4 data
    try:
        step4_data = TeamStep4Data.objects.get(matchup=matchup, team=user_team)
        team_text = step4_data.texts.get(text_number=text_number)
    except (TeamStep4Data.DoesNotExist, TeamText.DoesNotExist):
        messages.error(request, f"Text {text_number} not found.")
        return redirect('phoneme_density:step4', matchup_id=matchup_id)
    
    # Calculate frequencies for all phonemes
    text_frequencies = {}
    english_frequencies = {}
    phoneme_list = list(ENGLISH_PHONEME_FREQUENCIES.keys())
    
    for phoneme in phoneme_list:
        text_freq = calculate_phoneme_frequency(team_text.content, phoneme)
        english_freq = ENGLISH_PHONEME_FREQUENCIES[phoneme]
        
        text_frequencies[phoneme] = text_freq
        english_frequencies[phoneme] = english_freq
    
    # Calculate standard error for English frequencies using actual text length
    # Using formula: SE = sqrt(p * (1-p) / n) where n is the actual text length
    actual_text_length = len(team_text.content.replace(' ', ''))  # Character count excluding spaces
    standard_errors = {}
    
    for phoneme in phoneme_list:
        p = english_frequencies[phoneme] / 100  # Convert percentage to proportion
        se = math.sqrt(p * (1 - p) / actual_text_length) * 100  # Convert back to percentage
        standard_errors[phoneme] = se * 1.96  # 95% confidence interval
    
    # Calculate likelihood that each phoneme is the "overweight" target phoneme
    # Using z-score to measure how many standard deviations above the baseline each phoneme is
    phoneme_likelihoods = {}
    z_scores = {}
    
    for phoneme in phoneme_list:
        observed_freq = text_frequencies[phoneme]
        expected_freq = english_frequencies[phoneme]
        se_single = standard_errors[phoneme] / 1.96  # Get single standard error (not 95% CI)
        
        # Calculate z-score (how many standard deviations above baseline)
        z_score = (observed_freq - expected_freq) / se_single if se_single > 0 else 0
        z_scores[phoneme] = z_score
        
        # Convert z-score to likelihood using normal distribution
        # Higher z-scores = higher likelihood of being the target phoneme
        # Use max(0, z_score) so negative deviations don't contribute
        likelihood_score = max(0, z_score)
        phoneme_likelihoods[phoneme] = likelihood_score
    
    # Normalize likelihoods to percentages (sum to 100%)
    total_likelihood = sum(phoneme_likelihoods.values())
    if total_likelihood > 0:
        phoneme_probabilities = {
            phoneme: (likelihood / total_likelihood) * 100 
            for phoneme, likelihood in phoneme_likelihoods.items()
        }
    else:
        # If no phonemes are above baseline, assign equal probabilities
        phoneme_probabilities = {phoneme: 100/len(phoneme_list) for phoneme in phoneme_list}

    context = {
        'matchup': matchup,
        'team': user_team,
        'text_number': text_number,
        'team_text': team_text,
        'selected_phoneme': step4_data.selected_phoneme,
        'phoneme_list': json.dumps(phoneme_list),
        'text_frequencies': json.dumps(list(text_frequencies.values())),
        'english_frequencies': json.dumps(list(english_frequencies.values())),
        'standard_errors': json.dumps(list(standard_errors.values())),
        'phoneme_labels': json.dumps([f"/{p}/" for p in phoneme_list]),
        'z_scores': z_scores,
        'phoneme_probabilities': phoneme_probabilities,
        'phoneme_analysis': [
            {
                'phoneme': phoneme,
                'probability': phoneme_probabilities[phoneme],
                'z_score': z_scores[phoneme]
            }
            for phoneme in phoneme_list
        ],
    }
    
    return render(request, 'phoneme_density/text_analysis.html', context)


def analyze_combined_text(request, matchup_id):
    """Analyze combined text from texts 1, 3, 5, 7"""
    matchup = get_object_or_404(GameMatchup, id=matchup_id)
    
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('phoneme_density:step4', matchup_id=matchup_id)
    
    # Get combined text from form
    combined_text = request.POST.get('combined_text', '')
    selected_phoneme = request.POST.get('selected_phoneme', '')
    text_numbers = request.POST.get('text_numbers', '1,3,5,7')
    
    if not combined_text.strip():
        messages.error(request, "No text content found.")
        return redirect('phoneme_density:step4', matchup_id=matchup_id)
    
    # Get the user's team
    user_team = None
    if request.user in matchup.team1.members.all():
        user_team = matchup.team1
    elif request.user in matchup.team2.members.all():
        user_team = matchup.team2
    else:
        # Teachers can view any team's data
        user_team = matchup.team1  # Default for teachers
    
    # Calculate frequencies for all phonemes
    text_frequencies = {}
    english_frequencies = {}
    phoneme_list = list(ENGLISH_PHONEME_FREQUENCIES.keys())
    
    for phoneme in phoneme_list:
        text_freq = calculate_phoneme_frequency(combined_text, phoneme)
        english_freq = ENGLISH_PHONEME_FREQUENCIES[phoneme]
        
        text_frequencies[phoneme] = text_freq
        english_frequencies[phoneme] = english_freq
    
    # Calculate standard error for English frequencies using actual text length
    actual_text_length = len(combined_text.replace(' ', ''))  # Character count excluding spaces
    standard_errors = {}
    
    for phoneme in phoneme_list:
        p = english_frequencies[phoneme] / 100  # Convert percentage to proportion
        se = math.sqrt(p * (1 - p) / actual_text_length) * 100  # Convert back to percentage
        standard_errors[phoneme] = se * 1.96  # 95% confidence interval
    
    # Calculate likelihood that each phoneme is the "overweight" target phoneme
    phoneme_likelihoods = {}
    z_scores = {}
    
    for phoneme in phoneme_list:
        observed_freq = text_frequencies[phoneme]
        expected_freq = english_frequencies[phoneme]
        se_single = standard_errors[phoneme] / 1.96  # Get single standard error (not 95% CI)
        
        # Calculate z-score (how many standard deviations above baseline)
        z_score = (observed_freq - expected_freq) / se_single if se_single > 0 else 0
        z_scores[phoneme] = z_score
        
        # Convert z-score to likelihood using normal distribution
        likelihood_score = max(0, z_score)
        phoneme_likelihoods[phoneme] = likelihood_score
    
    # Normalize likelihoods to percentages (sum to 100%)
    total_likelihood = sum(phoneme_likelihoods.values())
    if total_likelihood > 0:
        phoneme_probabilities = {
            phoneme: (likelihood / total_likelihood) * 100 
            for phoneme, likelihood in phoneme_likelihoods.items()
        }
    else:
        # If no phonemes are above baseline, assign equal probabilities
        phoneme_probabilities = {phoneme: 100/len(phoneme_list) for phoneme in phoneme_list}

    # Create a mock text object for template compatibility
    mock_text = type('MockText', (), {
        'content': combined_text,
        'text_number': text_numbers,
    })()

    context = {
        'matchup': matchup,
        'team': user_team,
        'text_number': f"Combined ({text_numbers})",
        'team_text': mock_text,
        'selected_phoneme': selected_phoneme,
        'phoneme_list': json.dumps(phoneme_list),
        'text_frequencies': json.dumps(list(text_frequencies.values())),
        'english_frequencies': json.dumps(list(english_frequencies.values())),
        'standard_errors': json.dumps(list(standard_errors.values())),
        'phoneme_labels': json.dumps([f"/{p}/" for p in phoneme_list]),
        'z_scores': z_scores,
        'phoneme_probabilities': phoneme_probabilities,
        'phoneme_analysis': [
            {
                'phoneme': phoneme,
                'probability': phoneme_probabilities[phoneme],
                'z_score': z_scores[phoneme]
            }
            for phoneme in phoneme_list
        ],
        'is_combined_analysis': True,  # Flag to indicate this is combined analysis
        'combined_text_numbers': text_numbers,
    }
    
    return render(request, 'phoneme_density/text_analysis.html', context)
