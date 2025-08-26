from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.db import models
from .forms import (TeamForm, GameResourceForm, TeamInvitationForm, JoinTeamForm, SchoolForm, 
                   GameMatchupForm, SchoolTeamForm, TeamMemberForm, AiGameForm, GameStepForm, InstructionStepForm)
from .models import (AiGame, Team, TeamMembership, TeamGameParticipation, GameResource, TeamInvitation,
                     UserProfile, School, GameMatchup, InstructionStep, InstructionStepFeedback, GameStep)

def get_user_role(user):
    """Get user role from profile, defaulting to student"""
    if not user.is_authenticated:
        return 'student'
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=user, role='student')
        return 'student'

def can_create_games(user):
    """Check if user can create AI games (Admins only)"""
    if not user.is_authenticated:
        return False
    try:
        return user.profile.can_create_games
    except UserProfile.DoesNotExist:
        return False

def can_create_teams(user):
    """Check if user can create teams (Teachers and Admins)"""
    if not user.is_authenticated:
        return False
    try:
        return user.profile.can_create_teams
    except UserProfile.DoesNotExist:
        return False

def can_modify_syllabus(user):
    """Check if user can modify syllabus (Admins only)"""
    if not user.is_authenticated:
        return False
    try:
        return user.profile.can_modify_syllabus
    except UserProfile.DoesNotExist:
        return False

def is_admin(user):
    """Check if user is admin - kept for backward compatibility"""
    return can_modify_syllabus(user)

# Student Dashboard View
@login_required 
def student_dashboard(request):
    """Dashboard for students showing their assigned games"""
    user = request.user
    
    # Get all teams the user is a member of
    user_teams = user.teams.filter(is_active=True)
    
    # Get all games assigned to those teams through direct participation
    assigned_games = []
    for team in user_teams:
        team_participations = TeamGameParticipation.objects.filter(
            team=team,
            is_active=True
        ).select_related('ai_game')
        
        for participation in team_participations:
            game = participation.ai_game
            
            # Get current step if game has multiple steps
            current_step = None
            current_step_instructions = None
            progress = None
            progress_percentage = 0
            total_steps = 0
            completed_steps = 0
            
            if game.has_multiple_steps:
                # For team-based progress, we need to implement alternative logic
                # since teams don't directly track progress - this is done through matchups
                current_step = None
                current_step_instructions = None
                progress = None
                total_steps = game.get_ordered_steps().count()
                completed_steps = 0
                
                # Try to find a matchup for this team and game
                from django.db.models import Q
                matchup = GameMatchup.objects.filter(
                    Q(team1=team) | Q(team2=team),
                    ai_game=game,
                    status__in=['scheduled', 'in_progress']
                ).first()
                
                if matchup and hasattr(matchup, 'get_current_step'):
                    # Use matchup-based progress
                    try:
                        current_step_obj = matchup.get_current_step()
                        if current_step_obj and hasattr(current_step_obj, 'step_number'):
                            current_step = current_step_obj
                            current_step_instructions = current_step.get_instructions_for_user(user)
                        
                        # Count completed steps from matchup
                        for step_num in range(1, total_steps + 1):
                            step_progress = matchup.get_progress_for_step(step_num)
                            if step_progress and step_progress.is_completed:
                                completed_steps += 1
                    except:
                        pass
                
                if total_steps > 0:
                    progress_percentage = int((completed_steps / total_steps) * 100)
                
                # If we have no current step but the game has steps, try to get the first step
                if not current_step and total_steps > 0:
                    # Try to get the first step explicitly
                    first_step = game.get_ordered_steps().first()
                    if first_step:
                        current_step = first_step
                        current_step_instructions = current_step.get_instructions_for_user(user)
            
            assigned_games.append({
                'game': game,
                'team': team,
                'participation': participation,
                'current_step': current_step,
                'current_step_url': team.get_current_step_url(game),
                'first_step_url': None,  # No matchup available for participation-based games
                'current_step_instructions': current_step_instructions,
                'progress': progress,
                'progress_percentage': progress_percentage,
                'total_steps': total_steps,
                'completed_steps': completed_steps,
                'source': 'participation'
            })
    
    # Also get games assigned through matchups
    from .models import GameMatchup
    for team in user_teams:
        # Get matchups where this team is involved
        matchups = GameMatchup.objects.filter(
            models.Q(team1=team) | models.Q(team2=team),
            status__in=['scheduled', 'in_progress']
        ).select_related('ai_game', 'team1', 'team2')
        
        for matchup in matchups:
            game = matchup.ai_game
            
            # Check if this game is already in assigned_games from participation
            already_added = any(ag['game'].id == game.id and ag['team'].id == team.id for ag in assigned_games)
            if already_added:
                continue
            
            # Get current step if game has multiple steps
            current_step = None
            current_step_instructions = None
            current_step_url = None
            progress = None
            progress_percentage = 0
            total_steps = 0
            completed_steps = 0
            
            if game.has_multiple_steps:
                # For matchup-based games (like phoneme density), get progress from the matchup
                try:
                    # Get current step from matchup
                    current_step_number = 1
                    current_step = None
                    current_step_instructions = None
                    
                    if hasattr(matchup, 'get_current_step'):
                        current_step_obj = matchup.get_current_step()
                        if current_step_obj and hasattr(current_step_obj, 'step_number'):
                            current_step_number = current_step_obj.step_number
                            current_step = current_step_obj
                            current_step_instructions = current_step.get_instructions_for_user(user)
                        else:
                            current_step_number = 1
                            # Get the first step
                            first_step = game.get_step_by_number(1)
                            if first_step:
                                current_step = first_step
                                current_step_instructions = current_step.get_instructions_for_user(user)
                    
                    # Get total steps from the game itself
                    total_steps = game.steps.filter(is_active=True).count()
                    completed_steps = 0
                    for step_num in range(1, total_steps + 1):
                        step_progress = matchup.get_progress_for_step(step_num)
                        if step_progress and step_progress.is_completed:
                            completed_steps += 1
                    
                    if total_steps > 0:
                        progress_percentage = int((completed_steps / total_steps) * 100)
                    
                    # Get current step URL for this matchup using GameStep
                    current_step_url = None
                    if current_step_number:
                        try:
                            game_step = GameStep.objects.get(ai_game=matchup.ai_game, step_number=current_step_number)
                            current_step_url = game_step.get_url(matchup.id)
                        except GameStep.DoesNotExist:
                            current_step_url = None
                        
                except Exception as e:
                    # Fallback: Set defaults if matchup methods don't exist
                    current_step = None
                    current_step_instructions = None
                    progress = None
                    total_steps = game.steps.filter(is_active=True).count()
                    completed_steps = 0
                    if total_steps > 0:
                        progress_percentage = int((completed_steps / total_steps) * 100)
                    else:
                        progress_percentage = 0
                    current_step_url = team.get_current_step_url(game)
                
                # If we have no current step but the game has steps, try to get the first step
                if not current_step and total_steps > 0:
                    # Try to get the first step explicitly
                    first_step = game.get_ordered_steps().first()
                    if first_step:
                        current_step = first_step
                        current_step_instructions = current_step.get_instructions_for_user(user)
            
            # Calculate first_step_url
            first_step_url = None
            if game:
                first_step_url = game.get_first_step_url(matchup.id)
            
            assigned_games.append({
                'game': game,
                'team': team,
                'matchup': matchup,
                'current_step': current_step,
                'current_step_url': current_step_url,
                'first_step_url': first_step_url,
                'current_step_instructions': current_step_instructions,
                'progress': progress,
                'progress_percentage': progress_percentage,
                'total_steps': total_steps,
                'completed_steps': completed_steps,
                'source': 'matchup',
                'opponent_team': matchup.get_other_team(team)
            })
    
    # Get any pending team invitations
    pending_invitations = TeamInvitation.objects.filter(
        invited_user=user,
        accepted=None
    ).select_related('team', 'ai_game', 'invited_by')
    
    context = {
        'assigned_games': assigned_games,
        'pending_invitations': pending_invitations,
        'user_teams': user_teams,
        'is_student': user.profile.is_student if hasattr(user, 'profile') else True
    }
    
    return render(request, 'aigames/student_dashboard.html', context)

# Team Views
@login_required
def create_team(request):
    if not can_create_teams(request.user):
        messages.error(request, 'Only teachers and admins can create teams.')
        return redirect('aigames:list_teams')
    
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            # Security: assign team to user's school
            if hasattr(request.user, 'profile') and request.user.profile.school:
                team.school = request.user.profile.school
            else:
                messages.error(request, 'You must be associated with a school to create teams.')
                return redirect('aigames:list_teams')
            team.save()
            
            # Add creator as team admin
            TeamMembership.objects.create(
                team=team,
                user=request.user,
                role='admin'
            )
            
            messages.success(request, f'Team "{team.name}" created successfully!')
            return redirect('aigames:team_detail', team_id=team.id)
    else:
        form = TeamForm()
    return render(request, 'aigames/create_team.html', {'form': form})

@login_required
def list_teams(request):
    """List teams - filter by user's school for security"""
    if hasattr(request.user, 'profile') and request.user.profile.school:
        # Filter teams by user's school for security
        teams = Team.objects.filter(
            school=request.user.profile.school, 
            is_active=True
        ).order_by('name')
    else:
        # If user has no school profile, show no teams
        teams = Team.objects.none()
    
    user_teams = request.user.teams.filter(is_active=True)
    context = {
        'teams': teams,
        'user_teams': user_teams,
        'is_admin': is_admin(request.user)
    }
    return render(request, 'aigames/list_teams.html', context)

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id, is_active=True)
    
    # Security check: ensure user can access this team
    user_can_access = False
    is_member = False
    user_role = None
    
    # Check if user is member
    try:
        membership = TeamMembership.objects.get(team=team, user=request.user)
        is_member = True
        user_role = membership.role
        user_can_access = True
    except TeamMembership.DoesNotExist:
        pass
    
    # Check if user is admin or team is from same school
    if not user_can_access:
        if is_admin(request.user):
            user_can_access = True
        elif hasattr(request.user, 'profile') and request.user.profile.school == team.school:
            user_can_access = True
    
    if not user_can_access:
        messages.error(request, 'You do not have permission to view this team.')
        return redirect('aigames:list_teams')
    
    # Get games with current step URLs
    games_with_urls = []
    for game in team.games.all():
        games_with_urls.append({
            'game': game,
            'current_step_url': team.get_current_step_url(game)
        })
    
    context = {
        'team': team,
        'is_member': is_member,
        'user_role': user_role,
        'is_admin': is_admin(request.user),
        'games': team.games.all(),  # Keep for backward compatibility
        'games_with_urls': games_with_urls,  # New enhanced data
        'members': team.teammembership_set.all().select_related('user'),
    }
    return render(request, 'aigames/team_detail.html', context)

# Note: Letter density game views have been removed
# This functionality has been moved to the phoneme_density app

# User Role Management Views
@login_required
def manage_user_roles(request):
    """View for admins to manage user roles"""
    if not can_modify_syllabus(request.user):
        messages.error(request, 'Only admins can manage user roles.')
        return redirect('aigames:team_management_dashboard')
    
    from django.contrib.auth.models import User
    from .role_forms import BulkUserRoleForm
    
    if request.method == 'POST':
        form = BulkUserRoleForm(request.POST)
        if form.is_valid():
            users = form.cleaned_data['users']
            role = form.cleaned_data['role']
            
            updated_count = 0
            for user in users:
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.save()
                updated_count += 1
            
            messages.success(request, f'Updated {updated_count} user(s) to {role} role.')
            return redirect('aigames:manage_user_roles')
    else:
        form = BulkUserRoleForm()
    
    # Get all users with their profiles
    users_with_profiles = []
    for user in User.objects.all().order_by('username'):
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user, role='student')
        users_with_profiles.append((user, profile))
    
    context = {
        'form': form,
        'users_with_profiles': users_with_profiles,
        'role_choices': UserProfile.ROLE_CHOICES,
    }
    return render(request, 'aigames/manage_user_roles.html', context)

# School Management Views
@login_required
@user_passes_test(can_modify_syllabus)
def school_list(request):
    """List all schools"""
    schools = School.objects.all().order_by('name')
    context = {
        'schools': schools,
    }
    return render(request, 'aigames/school_list.html', context)

@login_required
@user_passes_test(can_modify_syllabus)
def create_school(request):
    """Create a new school"""
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()
            messages.success(request, f'School "{school.name}" created successfully!')
            return redirect('aigames:school_list')
    else:
        form = SchoolForm()
    
    return render(request, 'aigames/create_school.html', {'form': form})

@login_required
@user_passes_test(can_modify_syllabus)
def edit_school(request, school_id):
    """Edit an existing school"""
    school = get_object_or_404(School, id=school_id)
    
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            school = form.save()
            messages.success(request, f'School "{school.name}" updated successfully!')
            return redirect('aigames:school_list')
    else:
        form = SchoolForm(instance=school)
    
    context = {
        'form': form,
        'school': school,
    }
    return render(request, 'aigames/edit_school.html', context)

# School Management Views (Admin only)
@login_required
@user_passes_test(can_modify_syllabus)
def school_list(request):
    """List all schools"""
    schools = School.objects.all()
    context = {
        'schools': schools,
        'is_admin': is_admin(request.user)
    }
    return render(request, 'aigames/school_list.html', context)

@login_required
@user_passes_test(can_modify_syllabus)
def create_school(request):
    """Create a new school"""
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'School created successfully!')
            return redirect('school_list')
    else:
        form = SchoolForm()
    return render(request, 'aigames/create_school.html', {'form': form})

@login_required
@user_passes_test(can_modify_syllabus)
def edit_school(request, school_id):
    """Edit an existing school"""
    school = get_object_or_404(School, id=school_id)
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, 'School updated successfully!')
            return redirect('school_list')
    else:
        form = SchoolForm(instance=school)
    return render(request, 'aigames/edit_school.html', {'form': form, 'school': school})

# ==============================
# TEAM MANAGEMENT VIEWS
# ==============================

@login_required
@user_passes_test(can_create_teams)
def team_management_dashboard(request):
    """Teacher dashboard for managing teams and matchups"""
    user_school = request.user.profile.school
    
    # Get teams from the teacher's school
    school_teams = Team.objects.filter(school=user_school, is_active=True).order_by('name')
    
    # Get matchups created by this teacher or involving teams from their school
    all_school_matchups = GameMatchup.objects.filter(school=user_school).order_by('-created_at')
    
    # Get some statistics (before slicing)
    total_teams = school_teams.count()
    active_matchups = all_school_matchups.filter(status__in=['scheduled', 'in_progress']).count()
    
    # Get recent matchups for display (after getting statistics)
    school_matchups = all_school_matchups[:10]
    
    context = {
        'school_teams': school_teams,
        'school_matchups': school_matchups,
        'total_teams': total_teams,
        'active_matchups': active_matchups,
        'user_school': user_school,
    }
    return render(request, 'aigames/team_management_dashboard.html', context)

@login_required
@user_passes_test(can_create_teams)
def school_teams_list(request):
    """List all teams in the teacher's school"""
    user_school = request.user.profile.school
    teams = Team.objects.filter(school=user_school, is_active=True).order_by('name')
    
    context = {
        'teams': teams,
        'user_school': user_school,
    }
    return render(request, 'aigames/school_teams_list.html', context)

@login_required
@user_passes_test(can_create_teams)
def create_school_team(request):
    """Create a new team for the teacher's school"""
    user_school = request.user.profile.school
    
    if request.method == 'POST':
        form = SchoolTeamForm(school=user_school, data=request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.school = user_school
            team.created_by = request.user
            team.save()
            messages.success(request, f'Team "{team.name}" created successfully!')
            return redirect('aigames:school_teams_list')
    else:
        form = SchoolTeamForm(school=user_school)
    
    context = {
        'form': form,
        'user_school': user_school,
    }
    return render(request, 'aigames/create_school_team.html', context)

@login_required
@user_passes_test(can_create_teams)
def edit_school_team(request, team_id):
    """Edit a team from the teacher's school"""
    user_school = request.user.profile.school
    team = get_object_or_404(Team, id=team_id, school=user_school, is_active=True)
    
    # Initialize forms
    form = SchoolTeamForm(school=user_school, instance=team)
    member_form = TeamMemberForm(team=team, school=user_school)
    
    # Handle team member addition
    if request.method == 'POST' and 'add_member' in request.POST:
        member_form = TeamMemberForm(team=team, school=user_school, data=request.POST)
        if member_form.is_valid():
            user_to_add = member_form.cleaned_data['username']
            role = member_form.cleaned_data['role']
            
            # Create team membership
            from .models import TeamMembership
            TeamMembership.objects.create(
                team=team,
                user=user_to_add,
                role=role
            )
            messages.success(request, f'Added {user_to_add.username} to team "{team.name}" as {role}!')
            return redirect('aigames:edit_school_team', team_id=team.id)
        # If form is invalid, member_form will contain errors for display
    
    # Handle member removal
    elif request.method == 'POST' and 'remove_member' in request.POST:
        member_id = request.POST.get('member_id')
        if member_id:
            try:
                from .models import TeamMembership
                membership = TeamMembership.objects.get(
                    team=team, 
                    user_id=member_id
                )
                username = membership.user.username
                membership.delete()
                messages.success(request, f'Removed {username} from team "{team.name}"!')
                return redirect('aigames:edit_school_team', team_id=team.id)
            except TeamMembership.DoesNotExist:
                messages.error(request, 'Member not found in this team.')
        # Reset member form after removal attempt
        member_form = TeamMemberForm(team=team, school=user_school)
    
    # Handle team form submission
    elif request.method == 'POST':
        form = SchoolTeamForm(school=user_school, data=request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'Team "{team.name}" updated successfully!')
            return redirect('aigames:edit_school_team', team_id=team.id)
        # If form is invalid, form will contain errors for display
        # Reset member form since team form was submitted
        member_form = TeamMemberForm(team=team, school=user_school)
    
    # Get team members
    from .models import TeamMembership
    memberships = TeamMembership.objects.filter(team=team).select_related('user', 'user__profile').order_by('joined_at')
    
    context = {
        'form': form,
        'member_form': member_form,
        'team': team,
        'memberships': memberships,
        'user_school': user_school,
    }
    return render(request, 'aigames/edit_school_team.html', context)

@login_required
@user_passes_test(can_create_teams)
def delete_school_team(request, team_id):
    """Delete a team (only admins can delete teams, teachers can only deactivate)"""
    user_school = request.user.profile.school
    team = get_object_or_404(Team, id=team_id, school=user_school, is_active=True)
    
    # Check if user is admin or teacher
    is_admin = request.user.profile.role == 'admin'
    is_teacher = request.user.profile.role == 'teacher'
    
    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            if is_admin:
                # Admins can permanently delete the team
                team_name = team.name
                team.delete()
                messages.success(request, f'Team "{team_name}" has been permanently deleted.')
            else:
                # Teachers can only deactivate teams
                team.is_active = False
                team.save()
                messages.success(request, f'Team "{team.name}" has been deactivated.')
            return redirect('aigames:school_teams_list')
        else:
            return redirect('aigames:school_teams_list')
    
    # Get team statistics for confirmation dialog
    member_count = team.members.count()
    matchup_count = team.matchups_as_team1.count() + team.matchups_as_team2.count()
    
    context = {
        'team': team,
        'user_school': user_school,
        'is_admin': is_admin,
        'is_teacher': is_teacher,
        'member_count': member_count,
        'matchup_count': matchup_count,
    }
    return render(request, 'aigames/delete_school_team.html', context)

@login_required
@user_passes_test(can_create_teams)
def school_team_detail(request, team_id):
    """View details of a team including members and game participation"""
    user_school = request.user.profile.school
    team = get_object_or_404(Team, id=team_id, school=user_school, is_active=True)
    
    # Get team members
    memberships = TeamMembership.objects.filter(team=team).select_related('user', 'user__profile')
    
    # Get games this team is participating in
    participations = TeamGameParticipation.objects.filter(team=team, is_active=True).select_related('ai_game')
    
    # Get matchups involving this team
    team_matchups = GameMatchup.objects.filter(
        school=user_school
    ).filter(
        models.Q(team1=team) | models.Q(team2=team)
    ).order_by('-created_at')
    
    context = {
        'team': team,
        'memberships': memberships,
        'participations': participations,
        'team_matchups': team_matchups,
        'user_school': user_school,
    }
    return render(request, 'aigames/school_team_detail.html', context)

@login_required
@user_passes_test(can_create_teams)
def create_game_matchup(request):
    """Create a matchup between two teams for a game"""
    user_school = request.user.profile.school
    
    # Check for pre-selected game from URL parameter
    initial_game_id = request.GET.get('game')
    initial_game = None
    if initial_game_id:
        try:
            initial_game = AiGame.objects.get(id=initial_game_id)
        except AiGame.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = GameMatchupForm(user=request.user, initial_game=initial_game, data=request.POST)
        if form.is_valid():
            matchup = form.save(commit=False)
            matchup.school = user_school
            matchup.created_by = request.user
            matchup.save()
            messages.success(request, f'Matchup created: {matchup.team1.name} vs {matchup.team2.name} for {matchup.ai_game.title}')
            return redirect('aigames:game_matchups_list')
    else:
        form = GameMatchupForm(user=request.user, initial_game=initial_game)
    
    context = {
        'form': form,
        'user_school': user_school,
        'initial_game': initial_game,
    }
    return render(request, 'aigames/create_game_matchup.html', context)

@login_required
@user_passes_test(can_create_teams)
def game_matchups_list(request):
    """List all game matchups for the teacher's school"""
    user_school = request.user.profile.school
    matchups = GameMatchup.objects.filter(school=user_school).order_by('-created_at')
    
    context = {
        'matchups': matchups,
        'user_school': user_school,
    }
    return render(request, 'aigames/game_matchups_list.html', context)

@login_required
@user_passes_test(can_create_teams)
def game_matchup_detail(request, matchup_id):
    """View details of a specific game matchup and track progress"""
    user_school = request.user.profile.school
    matchup = get_object_or_404(GameMatchup, id=matchup_id, school=user_school)
    
    # Integrity check: Ensure validation-required steps are marked complete if both teams are validated
    if hasattr(request.user, 'profile') and (request.user.profile.is_teacher or request.user.profile.is_admin):
        completed_steps = matchup.check_and_complete_validation_steps()
        if completed_steps:
            from django.contrib import messages
            messages.info(request, f"Steps {', '.join(map(str, completed_steps))} were automatically marked as complete based on team validations.")
    
    # Get progress for both teams if it's a multi-step game
    team1_progress = []
    team2_progress = []
    
    if matchup.ai_game.has_multiple_steps:
        # For matchup-based games, progress is tracked through the matchup itself
        # We'll get step-by-step progress in the step_progress_info section below
        pass
    
    # Get step progression information for the matchup
    is_teacher = hasattr(request.user, 'profile') and (request.user.profile.is_teacher or request.user.profile.is_admin)
    current_step_number = 1
    step_progress_info = []
    
    # Get all GameSteps for this game
    game_steps = matchup.ai_game.get_ordered_steps()
    
    if game_steps.exists():
        # Check if this is a game with matchup-level step tracking
        if hasattr(matchup, 'get_current_step'):
            try:
                current_step = matchup.get_current_step()
                if current_step and hasattr(current_step, 'step_number'):
                    current_step_number = current_step.step_number
                else:
                    current_step_number = 1
            except:
                current_step_number = 1
                
        # Get progress for all steps using actual GameStep data
        for game_step in game_steps:
            step_num = game_step.step_number
            
            # Get progress for this step if the matchup supports it
            progress = None
            if hasattr(matchup, 'get_progress_for_step'):
                try:
                    progress = matchup.get_progress_for_step(step_num)
                except:
                    pass
            
            step_info = {
                'step_number': step_num,
                'game_step': game_step,  # Include the actual GameStep object
                'step_url': game_step.get_url(matchup.id),  # Generate the dynamic URL
                'is_completed': progress and progress.is_completed if progress else False,
                'is_current': step_num == current_step_number,
                'completed_at': progress.completed_at if progress and progress.is_completed else None,
                'can_complete': is_teacher and step_num == current_step_number and (not progress or not progress.is_completed),
                # Add team validation status
                'team1_validated': matchup.is_team_validated_for_step(matchup.team1, step_num),
                'team2_validated': matchup.is_team_validated_for_step(matchup.team2, step_num),
            }
            step_progress_info.append(step_info)
    
    context = {
        'matchup': matchup,
        'team1_progress': team1_progress,
        'team2_progress': team2_progress,
        'user_school': user_school,
        'is_teacher': is_teacher,
        'current_step_number': current_step_number,
        'step_progress_info': step_progress_info,
    }
    
    return render(request, 'aigames/game_matchup_detail.html', context)

@login_required
@user_passes_test(can_create_teams)
def update_matchup_status(request, matchup_id):
    """Update the status of a game matchup"""
    user_school = request.user.profile.school
    matchup = get_object_or_404(GameMatchup, id=matchup_id, school=user_school)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(GameMatchup.MATCHUP_STATUS_CHOICES):
            matchup.status = new_status
            
            # Set timestamps based on status
            if new_status == 'in_progress' and not matchup.started_at:
                from django.utils import timezone
                matchup.started_at = timezone.now()
            elif new_status == 'completed' and not matchup.completed_at:
                from django.utils import timezone
                matchup.completed_at = timezone.now()
            
            matchup.save()
            messages.success(request, f'Matchup status updated to {matchup.get_status_display()}')
        
        return redirect('aigames:game_matchup_detail', matchup_id=matchup.id)

@login_required
@user_passes_test(can_create_teams)
@require_POST
def complete_matchup_step_from_detail(request, matchup_id, step_number):
    """Complete a step from the matchup detail page"""
    user_school = request.user.profile.school
    matchup = get_object_or_404(GameMatchup, id=matchup_id, school=user_school)
    
    # Only teachers can complete steps
    if not (hasattr(request.user, 'profile') and (request.user.profile.is_teacher or request.user.profile.is_admin)):
        messages.error(request, "Only teachers can mark steps as completed.")
        return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    
    # Complete the step
    try:
        progress = matchup.complete_step(step_number)
        if progress:
            messages.success(request, f"Step {step_number} marked as completed!")
        else:
            messages.error(request, f"Could not complete step {step_number}.")
    except Exception as e:
        messages.error(request, f"Error completing step: {str(e)}")
    
    return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)

@login_required
@user_passes_test(can_create_teams)
@require_POST
def validate_team_step(request, matchup_id, step_number, team_id):
    """Validate a specific team's completion of a step"""
    user_school = request.user.profile.school
    matchup = get_object_or_404(GameMatchup, id=matchup_id, school=user_school)
    team = get_object_or_404(Team, id=team_id)
    
    # Only teachers can validate steps
    if not (hasattr(request.user, 'profile') and (request.user.profile.role == 'teacher' or request.user.profile.role == 'admin')):
        messages.error(request, "Only teachers can validate team steps.")
        return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    
    # Verify the team is part of this matchup
    if team not in [matchup.team1, matchup.team2]:
        messages.error(request, "Team is not part of this matchup.")
        return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    
    # Get the game step
    game_step = matchup.ai_game.get_step_by_number(step_number)
    if not game_step:
        messages.error(request, f"Step {step_number} not found.")
        return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    
    # Check if step requires validation
    if not game_step.requires_validation:
        messages.warning(request, f"Step {step_number} does not require validation.")
        return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    
    # Get or create team validation record
    from .models import TeamStepValidation
    validation, created = TeamStepValidation.objects.get_or_create(
        matchup=matchup,
        team=team,
        game_step=game_step
    )
    
    # Check if already validated
    if validation.is_validated:
        messages.info(request, f"Step {step_number} for {team.name} is already validated.")
        return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)
    
    # Mark as validated
    try:
        validation.validate(request.user)
        messages.success(request, f"Step {step_number} validated for {team.name}!")
        
        # Check if step is now complete (both teams validated)
        step_progress = matchup.get_progress_for_step(step_number)
        if step_progress and step_progress.is_completed:
            messages.info(request, f"Step {step_number} is now complete - both teams validated!")
        else:
            # Check the other team's validation status
            other_team = matchup.team2 if team == matchup.team1 else matchup.team1
            other_team_validated = matchup.is_team_validated_for_step(other_team, step_number)
            if not other_team_validated:
                messages.info(request, f"Waiting for {other_team.name} validation to complete step {step_number}.")
            
    except Exception as e:
        messages.error(request, f"Error validating step: {str(e)}")
    
    return redirect('aigames:game_matchup_detail', matchup_id=matchup_id)

@login_required
@user_passes_test(can_create_teams)
def teacher_game_instructions(request, game_id):
    """Show teacher-specific instructions for a game"""
    game = get_object_or_404(AiGame, id=game_id)
    user_school = request.user.profile.school
    is_admin = request.user.profile.role == 'admin'
    
    # Handle admin instruction editing
    if request.method == 'POST' and is_admin:
        step_id = request.POST.get('step_id')
        instruction_id = request.POST.get('instruction_id')
        content = request.POST.get('content', '').strip()
        title = request.POST.get('title', '').strip()
        
        if step_id:
            try:
                game_step = GameStep.objects.get(id=step_id, ai_game=game)
                
                if instruction_id:
                    # Update existing instruction
                    instruction = InstructionStep.objects.get(id=instruction_id, game_step=game_step)
                    instruction.title = title
                    instruction.content = content
                    instruction.save()
                    messages.success(request, 'Instruction updated successfully!')
                else:
                    # Create new instruction
                    if title and content:
                        InstructionStep.objects.create(
                            game_step=game_step,
                            title=title,
                            content=content,
                            role='teacher',
                            is_active=True
                        )
                        messages.success(request, 'New instruction created successfully!')
                    else:
                        messages.error(request, 'Title and content are required for new instructions.')
                        
            except (GameStep.DoesNotExist, InstructionStep.DoesNotExist):
                messages.error(request, 'Step or instruction not found.')
            except Exception as e:
                messages.error(request, f'Error saving instruction: {str(e)}')
        
        return redirect('aigames:teacher_game_instructions', game_id=game_id)
    
    # Get the unit that has this game associated
    from syllabus.models import Unit
    unit = Unit.objects.filter(ai_game=game).first()
    
    # Get teams from teacher's school that could play this game
    school_teams = Team.objects.filter(school=user_school, is_active=True)
    
    # Get existing matchups for this game in the teacher's school
    existing_matchups = GameMatchup.objects.filter(
        ai_game=game, 
        school=user_school
    ).order_by('-created_at')[:5]
    
    # Get game steps with teacher instructions
    game_steps_data = []
    game_steps = GameStep.objects.filter(ai_game=game).order_by('step_number')
    
    for step in game_steps:
        teacher_instructions = step.instruction_steps.filter(
            role='teacher', 
            is_active=True
        ).order_by('id')
        
        game_steps_data.append({
            'step': step,
            'teacher_instructions': teacher_instructions
        })
    
    context = {
        'game': game,
        'unit': unit,  # Add unit to context
        'user_school': user_school,
        'school_teams': school_teams,
        'existing_matchups': existing_matchups,
        'game_steps': game_steps_data,
        'is_admin': is_admin,
    }
    return render(request, 'aigames/teacher_game_instructions.html', context)

# Instruction Step Views

@login_required
def game_instructions(request, game_id):
    """Display all instruction steps for a game"""
    game = get_object_or_404(AiGame, id=game_id)
    
    # Check if user is admin to show enhanced view
    is_admin = hasattr(request.user, 'profile') and request.user.profile.is_admin
    
    if is_admin:
        # Admin view: Show GameStep structure with both teacher and student instructions
        game_steps_data = []
        
        for game_step in game.get_ordered_steps():
            # Get both teacher and student instruction chains
            student_chain_instructions = game_step.get_instruction_chain_for_role('student')
            teacher_chain_instructions = game_step.get_instruction_chain_for_role('teacher')
            
            # Get ALL instructions for this step (including orphaned ones)
            all_student_instructions = game_step.instruction_steps.filter(role='student', is_active=True).order_by('id')
            all_teacher_instructions = game_step.instruction_steps.filter(role='teacher', is_active=True).order_by('id')
            
            # Helper function to process instructions and identify orphans
            def process_instructions(chain_instructions, all_instructions):
                data = []
                chain_ids = set(inst.id for inst in chain_instructions)
                
                # Add chained instructions first (in order)
                for inst in chain_instructions:
                    user_feedback = None
                    if request.user.is_authenticated:
                        try:
                            user_feedback = InstructionStepFeedback.objects.get(
                                instruction_step=inst,
                                user=request.user
                            )
                        except InstructionStepFeedback.DoesNotExist:
                            pass
                    
                    data.append({
                        'instruction': inst,
                        'user_feedback': user_feedback,
                        'feedback_summary': inst.get_feedback_summary(),
                        'is_orphaned': False,
                        'is_in_chain': True,
                        'chain_position': len(data) + 1,
                    })
                
                # Add orphaned instructions
                orphaned_instructions = [inst for inst in all_instructions if inst.id not in chain_ids]
                
                # Special case: if there's only one orphaned instruction and no chain, don't mark it as orphaned
                if len(orphaned_instructions) == 1 and len(chain_instructions) == 0:
                    inst = orphaned_instructions[0]
                    user_feedback = None
                    if request.user.is_authenticated:
                        try:
                            user_feedback = InstructionStepFeedback.objects.get(
                                instruction_step=inst,
                                user=request.user
                            )
                        except InstructionStepFeedback.DoesNotExist:
                            pass
                    
                    data.append({
                        'instruction': inst,
                        'user_feedback': user_feedback,
                        'feedback_summary': inst.get_feedback_summary(),
                        'is_orphaned': False,  # Don't mark as orphaned if it's the only one
                        'is_in_chain': False,
                        'chain_position': None,
                    })
                else:
                    # Multiple orphaned or there's already a chain
                    for inst in orphaned_instructions:
                        user_feedback = None
                        if request.user.is_authenticated:
                            try:
                                user_feedback = InstructionStepFeedback.objects.get(
                                    instruction_step=inst,
                                    user=request.user
                                )
                            except InstructionStepFeedback.DoesNotExist:
                                pass
                        
                        data.append({
                            'instruction': inst,
                            'user_feedback': user_feedback,
                            'feedback_summary': inst.get_feedback_summary(),
                            'is_orphaned': True,
                            'is_in_chain': False,
                            'chain_position': None,
                        })
                
                return data
            
            student_data = process_instructions(student_chain_instructions, all_student_instructions)
            teacher_data = process_instructions(teacher_chain_instructions, all_teacher_instructions)
            
            game_steps_data.append({
                'game_step': game_step,
                'student_instructions': student_data,
                'teacher_instructions': teacher_data,
            })
        
        context = {
            'game': game,
            'game_steps_data': game_steps_data,
            'is_admin_view': True,
            'user_role': 'admin',
        }
        return render(request, 'aigames/game_instructions_admin.html', context)
    
    else:
        # Regular user view: Show instructions for their role only
        instruction_steps = []
        
        # Get user role to determine which instructions to show
        user_role = 'student'
        if hasattr(request.user, 'profile'):
            if request.user.profile.is_teacher or request.user.profile.is_admin:
                user_role = 'teacher'
        
        # Get all game steps ordered by step number
        for game_step in game.get_ordered_steps():
            # Get instruction chain for this user's role
            step_instructions = game_step.get_instruction_chain_for_role(user_role)
            
            for step in step_instructions:
                if step.is_visible_to_user(request.user):
                    # Get user's feedback for this step if it exists
                    user_feedback = None
                    if request.user.is_authenticated:
                        try:
                            user_feedback = InstructionStepFeedback.objects.get(
                                instruction_step=step,
                                user=request.user
                            )
                        except InstructionStepFeedback.DoesNotExist:
                            pass
                    
                    step_data = {
                        'step': step,
                        'user_feedback': user_feedback,
                        'feedback_summary': step.get_feedback_summary(),
                        'game_step': game_step,  # Include game step info
                        'is_teacher': request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher')
                    }
                    instruction_steps.append(step_data)

        context = {
            'game': game,
            'instruction_steps': instruction_steps,
            'is_admin_view': False,
            'user_role': get_user_role(request.user),
        }
        return render(request, 'aigames/game_instructions.html', context)@login_required
def instruction_step_detail(request, step_id):
    """Display detailed view of a single instruction step"""
    step = get_object_or_404(InstructionStep, id=step_id, is_active=True)
    
    # Check if user can see this step
    if not step.is_visible_to_user(request.user):
        raise Http404("Instruction step not found")
    
    # Get user's feedback if it exists
    user_feedback = None
    if request.user.is_authenticated:
        try:
            user_feedback = InstructionStepFeedback.objects.get(
                instruction_step=step,
                user=request.user
            )
        except InstructionStepFeedback.DoesNotExist:
            pass
    
    # Get other steps for navigation - need to collect from all game steps
    all_steps = []
    user_role = 'student'
    if hasattr(request.user, 'profile'):
        if request.user.profile.is_teacher or request.user.profile.is_admin:
            user_role = 'teacher'
    
    # Collect all visible instruction steps from all game steps
    for game_step in step.game_step.ai_game.get_ordered_steps():
        step_instructions = game_step.get_instruction_chain_for_role(user_role)
        all_steps.extend(step_instructions)
    
    visible_steps = [s for s in all_steps if s.is_visible_to_user(request.user)]
    
    # Find current step index for navigation
    current_index = next((i for i, s in enumerate(visible_steps) if s.id == step.id), 0)
    previous_step = visible_steps[current_index - 1] if current_index > 0 else None
    next_step = visible_steps[current_index + 1] if current_index < len(visible_steps) - 1 else None
    
    context = {
        'step': step,
        'user_feedback': user_feedback,
        'feedback_summary': step.get_feedback_summary(),
        'previous_step': previous_step,
        'next_step': next_step,
        'step_number': current_index + 1,
        'total_steps': len(visible_steps),
    }
    return render(request, 'aigames/instruction_step_detail.html', context)

@login_required
def submit_instruction_feedback(request, step_id):
    """Submit thumbs up/down feedback for an instruction step"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    step = get_object_or_404(InstructionStep, id=step_id, is_active=True)
    
    # Check if user can see this step
    if not step.is_visible_to_user(request.user):
        return JsonResponse({'error': 'Step not found'}, status=404)
    
    is_helpful = request.POST.get('is_helpful') == 'true'
    feedback_comment = request.POST.get('feedback_comment', '').strip()
    
    # Create or update feedback
    feedback, created = InstructionStepFeedback.objects.update_or_create(
        instruction_step=step,
        user=request.user,
        defaults={
            'is_helpful': is_helpful,
            'feedback_comment': feedback_comment
        }
    )
    
    # Get updated feedback summary
    summary = step.get_feedback_summary()
    
    response_data = {
        'success': True,
        'feedback_type': 'helpful' if is_helpful else 'not_helpful',
        'summary': summary,
        'message': 'Thank you for your feedback!' if created else 'Your feedback has been updated.'
    }
    
    return JsonResponse(response_data)

@login_required
@user_passes_test(lambda u: u.profile.is_admin if hasattr(u, 'profile') else False)
def admin_instruction_steps(request, game_id):
    """Admin view for managing instruction steps - redirects to enhanced admin view"""
    # Redirect to the enhanced admin interface
    from django.shortcuts import redirect
    return redirect('aigames:game_instructions', game_id=game_id)

@login_required
@user_passes_test(lambda u: u.profile.is_admin if hasattr(u, 'profile') else False)
def problematic_steps_dashboard(request):
    """Admin dashboard for monitoring problematic instruction steps across all games"""
    from django.utils import timezone
    from datetime import timedelta
    
    # Get all active instruction steps
    all_steps = InstructionStep.objects.filter(is_active=True).select_related('game_step__ai_game')
    
    # Categorize steps
    problematic_steps = []
    recent_issues_steps = []
    low_feedback_steps = []
    good_steps = []
    
    for step in all_steps:
        summary = step.get_feedback_summary()
        
        if step.is_problematic():
            problematic_steps.append({
                'step': step,
                'summary': summary,
                'reasons': step.get_problematic_reasons()
            })
        elif step.has_recent_negative_feedback():
            recent_issues_steps.append({
                'step': step,
                'summary': summary,
                'reasons': step.get_problematic_reasons()
            })
        elif summary['total'] == 0:
            low_feedback_steps.append({
                'step': step,
                'summary': summary
            })
        else:
            good_steps.append({
                'step': step,
                'summary': summary
            })
    
    # Get overall statistics
    total_steps = all_steps.count()
    total_feedback = sum(step.get_feedback_summary()['total'] for step in all_steps)
    
    # Get recent feedback activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_feedback_count = InstructionStepFeedback.objects.filter(
        created_at__gte=week_ago
    ).count()
    
    context = {
        'problematic_steps': problematic_steps,
        'recent_issues_steps': recent_issues_steps,
        'low_feedback_steps': low_feedback_steps,
        'good_steps': good_steps,
        'stats': {
            'total_steps': total_steps,
            'problematic_count': len(problematic_steps),
            'recent_issues_count': len(recent_issues_steps),
            'no_feedback_count': len(low_feedback_steps),
            'good_count': len(good_steps),
            'total_feedback': total_feedback,
            'recent_feedback_count': recent_feedback_count,
        }
    }
    return render(request, 'aigames/problematic_steps_dashboard.html', context)


# Instruction Management Views (KEPT - needed for creating teacher/student instructions)
@login_required
@user_passes_test(can_create_games)
def manage_step_instructions(request, game_id, step_id):
    """Manage instructions for a specific game step"""
    game = get_object_or_404(AiGame, id=game_id)
    step = get_object_or_404(GameStep, id=step_id, ai_game=game)
    
    # Get instructions grouped by role
    student_instructions = step.instruction_steps.filter(role='student', is_active=True).order_by('id')
    teacher_instructions = step.instruction_steps.filter(role='teacher', is_active=True).order_by('id')
    
    context = {
        'game': game,
        'step': step,
        'student_instructions': student_instructions,
        'teacher_instructions': teacher_instructions
    }
    return render(request, 'aigames/manage_step_instructions.html', context)

@login_required
@user_passes_test(can_create_games)
def create_instruction(request, game_id, step_id):
    """Create a new instruction for a game step"""
    game = get_object_or_404(AiGame, id=game_id)
    step = get_object_or_404(GameStep, id=step_id, ai_game=game)
    
    if request.method == 'POST':
        form = InstructionStepForm(request.POST)
        if form.is_valid():
            instruction = form.save(commit=False)
            instruction.game_step = step
            instruction.created_by = request.user
            instruction.save()
            messages.success(request, f'Instruction "{instruction.title}" created successfully!')
            return redirect('aigames:manage_step_instructions', game_id=game.id, step_id=step.id)
    else:
        form = InstructionStepForm()
    
    context = {
        'form': form,
        'game': game,
        'step': step,
        'title': f'Add Instruction to {step.title}'
    }
    return render(request, 'aigames/instruction_form.html', context)

@login_required
@user_passes_test(can_create_games)
def edit_instruction(request, game_id, step_id, instruction_id):
    """Edit an existing instruction"""
    game = get_object_or_404(AiGame, id=game_id)
    step = get_object_or_404(GameStep, id=step_id, ai_game=game)
    instruction = get_object_or_404(InstructionStep, id=instruction_id, game_step=step)
    
    if request.method == 'POST':
        form = InstructionStepForm(request.POST, instance=instruction)
        if form.is_valid():
            instruction = form.save()
            messages.success(request, f'Instruction "{instruction.title}" updated successfully!')
            return redirect('aigames:manage_step_instructions', game_id=game.id, step_id=step.id)
    else:
        form = InstructionStepForm(instance=instruction)
    
    context = {
        'form': form,
        'game': game,
        'step': step,
        'instruction': instruction,
        'title': f'Edit {instruction.title}'
    }
    return render(request, 'aigames/instruction_form.html', context)

@login_required
@user_passes_test(can_create_games)
def delete_instruction(request, game_id, step_id, instruction_id):
    """Delete an instruction"""
    game = get_object_or_404(AiGame, id=game_id)
    step = get_object_or_404(GameStep, id=step_id, ai_game=game)
    instruction = get_object_or_404(InstructionStep, id=instruction_id, game_step=step)
    
    if request.method == 'POST':
        instruction_title = instruction.title
        instruction.delete()
        messages.success(request, f'Instruction "{instruction_title}" deleted successfully!')
        return redirect('aigames:manage_step_instructions', game_id=game.id, step_id=step.id)
    
    context = {
        'game': game,
        'step': step,
        'instruction': instruction
    }
    return render(request, 'aigames/confirm_delete_instruction.html', context)


# Admin Instruction Management Views

@login_required
def edit_student_instructions(request):
    """Admin view to edit student instructions for selected game"""
    if not request.user.profile.can_modify_syllabus:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('curriculum_list')
    
    # Get selected game from URL parameter or form
    selected_game_id = request.GET.get('game') or request.POST.get('selected_game')
    selected_game = None
    
    if selected_game_id:
        try:
            selected_game = AiGame.objects.get(id=selected_game_id)
        except AiGame.DoesNotExist:
            selected_game = None
    
    # Handle POST request (save instructions)
    if request.method == 'POST' and selected_game:
        from django.http import JsonResponse
        import json
        
        try:
            instruction_mappings = {}
            
            # Process form data
            for key, value in request.POST.items():
                if key.startswith('instruction_') and '_title' in key:
                    # Extract instruction ID and field type
                    parts = key.split('_')
                    instruction_id = '_'.join(parts[1:-1])  # Handle IDs like "new_1000"
                    
                    # Get title and content
                    title = value.strip()
                    content_key = f"instruction_{instruction_id}_content"
                    content = request.POST.get(content_key, '').strip()
                    role_key = f"instruction_{instruction_id}_role"
                    role = request.POST.get(role_key, 'student')
                    step_id_key = f"instruction_{instruction_id}_step_id"
                    step_id = request.POST.get(step_id_key)
                    
                    if not step_id:
                        continue
                    
                    try:
                        step = GameStep.objects.get(id=step_id, ai_game=selected_game)
                    except GameStep.DoesNotExist:
                        continue
                    
                    # Check if this is a new instruction
                    if instruction_id.startswith('new_'):
                        # Create new instruction if title or content is provided
                        if title or content:
                            new_instruction = InstructionStep.objects.create(
                                game_step=step,
                                title=title or "Untitled Instruction",
                                content=content,
                                role=role,
                                created_by=request.user
                            )
                            instruction_mappings[instruction_id] = new_instruction.id
                    else:
                        # Update existing instruction
                        try:
                            instruction = InstructionStep.objects.get(id=instruction_id, game_step__ai_game=selected_game)
                            instruction.title = title or instruction.title
                            instruction.content = content
                            instruction.save()
                        except InstructionStep.DoesNotExist:
                            continue
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'instruction_mappings': instruction_mappings,
                    'message': 'Instructions saved successfully!'
                })
            else:
                messages.success(request, 'Instructions saved successfully!')
                from django.urls import reverse
                return redirect(reverse('aigames:edit_student_instructions') + f'?game={selected_game.id}')
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in edit_student_instructions: {str(e)}", exc_info=True)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            else:
                messages.error(request, f'Error saving instructions: {str(e)}')
    
    # GET request - display game selection and instructions
    all_games = AiGame.objects.all().order_by('title')
    game_data = None
    
    if selected_game:
        game_steps_data = []
        game_steps = GameStep.objects.filter(ai_game=selected_game).order_by('step_number')
        
        for step in game_steps:
            student_instructions = step.instruction_steps.filter(
                role='student', 
                is_active=True
            ).order_by('id')
            
            game_steps_data.append({
                'step': step,
                'student_instructions': student_instructions
            })
        
        if game_steps_data:  # Only include if game has steps
            game_data = {
                'game': selected_game,
                'game_steps': game_steps_data
            }
    
    context = {
        'all_games': all_games,
        'selected_game': selected_game,
        'game_data': game_data,
        'instruction_type': 'student'
    }
    return render(request, 'aigames/edit_selected_instructions.html', context)


@login_required
def edit_teacher_instructions(request):
    """Admin view to edit teacher instructions for selected game"""
    if not request.user.profile.can_modify_syllabus:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('curriculum_list')
    
    # Get selected game from URL parameter or form
    selected_game_id = request.GET.get('game') or request.POST.get('selected_game')
    selected_game = None
    
    if selected_game_id:
        try:
            selected_game = AiGame.objects.get(id=selected_game_id)
        except AiGame.DoesNotExist:
            selected_game = None
    
    # Handle POST request (save instructions)
    if request.method == 'POST' and selected_game:
        from django.http import JsonResponse
        import json
        
        try:
            instruction_mappings = {}
            
            # Process form data
            for key, value in request.POST.items():
                if key.startswith('instruction_') and '_title' in key:
                    # Extract instruction ID and field type
                    parts = key.split('_')
                    instruction_id = '_'.join(parts[1:-1])  # Handle IDs like "new_1000"
                    
                    # Get title and content
                    title = value.strip()
                    content_key = f"instruction_{instruction_id}_content"
                    content = request.POST.get(content_key, '').strip()
                    role_key = f"instruction_{instruction_id}_role"
                    role = request.POST.get(role_key, 'teacher')
                    step_id_key = f"instruction_{instruction_id}_step_id"
                    step_id = request.POST.get(step_id_key)
                    
                    if not step_id:
                        continue
                    
                    try:
                        step = GameStep.objects.get(id=step_id, ai_game=selected_game)
                    except GameStep.DoesNotExist:
                        continue
                    
                    # Check if this is a new instruction
                    if instruction_id.startswith('new_'):
                        # Create new instruction if title or content is provided
                        if title or content:
                            new_instruction = InstructionStep.objects.create(
                                game_step=step,
                                title=title or "Untitled Instruction",
                                content=content,
                                role=role,
                                created_by=request.user
                            )
                            instruction_mappings[instruction_id] = new_instruction.id
                    else:
                        # Update existing instruction
                        try:
                            instruction = InstructionStep.objects.get(id=instruction_id, game_step__ai_game=selected_game)
                            instruction.title = title or instruction.title
                            instruction.content = content
                            instruction.save()
                        except InstructionStep.DoesNotExist:
                            continue
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'instruction_mappings': instruction_mappings,
                    'message': 'Instructions saved successfully!'
                })
            else:
                messages.success(request, 'Instructions saved successfully!')
                from django.urls import reverse
                return redirect(reverse('aigames:edit_teacher_instructions') + f'?game={selected_game.id}')
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in edit_teacher_instructions: {str(e)}", exc_info=True)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            else:
                messages.error(request, f'Error saving instructions: {str(e)}')
    
    # GET request - display game selection and instructions
    all_games = AiGame.objects.all().order_by('title')
    game_data = None
    
    if selected_game:
        game_steps_data = []
        game_steps = GameStep.objects.filter(ai_game=selected_game).order_by('step_number')
        
        for step in game_steps:
            teacher_instructions = step.instruction_steps.filter(
                role='teacher', 
                is_active=True
            ).order_by('id')
            
            game_steps_data.append({
                'step': step,
                'teacher_instructions': teacher_instructions
            })
        
        if game_steps_data:  # Only include if game has steps
            game_data = {
                'game': selected_game,
                'game_steps': game_steps_data
            }
    
    context = {
        'all_games': all_games,
        'selected_game': selected_game,
        'game_data': game_data,
        'instruction_type': 'teacher'
    }
    return render(request, 'aigames/edit_selected_instructions.html', context)


@login_required
def edit_student_instructions_for_game(request, game_id):
    """Admin view to edit student instructions for a specific game with carousel"""
    if not request.user.profile.can_modify_syllabus:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('curriculum_list')
    
    game = get_object_or_404(AiGame, id=game_id)
    
    # Handle POST request (save instructions)
    if request.method == 'POST':
        from django.http import JsonResponse
        import json
        
        try:
            instruction_mappings = {}
            
            # Process form data
            for key, value in request.POST.items():
                if key.startswith('instruction_') and '_title' in key:
                    # Extract instruction ID and field type
                    parts = key.split('_')
                    instruction_id = '_'.join(parts[1:-1])  # Handle IDs like "new_1000"
                    
                    # Get title and content
                    title = value.strip()
                    content_key = f"instruction_{instruction_id}_content"
                    content = request.POST.get(content_key, '').strip()
                    role_key = f"instruction_{instruction_id}_role"
                    role = request.POST.get(role_key, 'student')
                    step_id_key = f"instruction_{instruction_id}_step_id"
                    step_id = request.POST.get(step_id_key)
                    
                    if not step_id:
                        continue
                        
                    step = get_object_or_404(GameStep, id=step_id, ai_game=game)
                    
                    # Check if this is a new instruction
                    if instruction_id.startswith('new_'):
                        # Create new instruction if title or content is provided
                        if title or content:
                            new_instruction = InstructionStep.objects.create(
                                game_step=step,
                                title=title or "Untitled Instruction",
                                content=content,
                                role=role,
                                created_by=request.user
                            )
                            instruction_mappings[instruction_id] = new_instruction.id
                    else:
                        # Update existing instruction
                        try:
                            instruction = InstructionStep.objects.get(id=instruction_id, game_step__ai_game=game)
                            instruction.title = title or instruction.title
                            instruction.content = content
                            instruction.save()
                        except InstructionStep.DoesNotExist:
                            continue
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'instruction_mappings': instruction_mappings,
                    'message': 'Instructions saved successfully!'
                })
            else:
                messages.success(request, 'Instructions saved successfully!')
                return redirect('aigames:edit_student_instructions_for_game', game_id=game.id)
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            else:
                messages.error(request, f'Error saving instructions: {str(e)}')
    
    # GET request - display the form
    # Get game steps with student instructions
    game_steps_data = []
    game_steps = GameStep.objects.filter(ai_game=game).order_by('step_number')
    
    for step in game_steps:
        student_instructions = step.instruction_steps.filter(
            role='student', 
            is_active=True
        ).order_by('id')
        
        game_steps_data.append({
            'step': step,
            'student_instructions': student_instructions
        })
    
    context = {
        'game': game,
        'game_steps': game_steps_data,
        'instruction_type': 'student'
    }
    return render(request, 'aigames/edit_instructions_carousel.html', context)


@login_required
def edit_teacher_instructions_for_game(request, game_id):
    """Admin view to edit teacher instructions for a specific game with carousel"""
    if not request.user.profile.can_modify_syllabus:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('curriculum_list')
    
    game = get_object_or_404(AiGame, id=game_id)
    
    # Handle POST request (save instructions)
    if request.method == 'POST':
        from django.http import JsonResponse
        import json
        
        try:
            instruction_mappings = {}
            
            # Process form data
            for key, value in request.POST.items():
                if key.startswith('instruction_') and '_title' in key:
                    # Extract instruction ID and field type
                    parts = key.split('_')
                    instruction_id = '_'.join(parts[1:-1])  # Handle IDs like "new_1000"
                    
                    # Get title and content
                    title = value.strip()
                    content_key = f"instruction_{instruction_id}_content"
                    content = request.POST.get(content_key, '').strip()
                    role_key = f"instruction_{instruction_id}_role"
                    role = request.POST.get(role_key, 'teacher')
                    step_id_key = f"instruction_{instruction_id}_step_id"
                    step_id = request.POST.get(step_id_key)
                    
                    if not step_id:
                        continue
                        
                    step = get_object_or_404(GameStep, id=step_id, ai_game=game)
                    
                    # Check if this is a new instruction
                    if instruction_id.startswith('new_'):
                        # Create new instruction if title or content is provided
                        if title or content:
                            new_instruction = InstructionStep.objects.create(
                                game_step=step,
                                title=title or "Untitled Instruction",
                                content=content,
                                role=role,
                                created_by=request.user
                            )
                            instruction_mappings[instruction_id] = new_instruction.id
                    else:
                        # Update existing instruction
                        try:
                            instruction = InstructionStep.objects.get(id=instruction_id, game_step__ai_game=game)
                            instruction.title = title or instruction.title
                            instruction.content = content
                            instruction.save()
                        except InstructionStep.DoesNotExist:
                            continue
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'instruction_mappings': instruction_mappings,
                    'message': 'Instructions saved successfully!'
                })
            else:
                messages.success(request, 'Instructions saved successfully!')
                return redirect('aigames:edit_teacher_instructions_for_game', game_id=game.id)
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            else:
                messages.error(request, f'Error saving instructions: {str(e)}')
    
    # GET request - display the form
    # Get game steps with teacher instructions
    game_steps_data = []
    game_steps = GameStep.objects.filter(ai_game=game).order_by('step_number')
    
    for step in game_steps:
        teacher_instructions = step.instruction_steps.filter(
            role='teacher', 
            is_active=True
        ).order_by('id')
        
        game_steps_data.append({
            'step': step,
            'teacher_instructions': teacher_instructions
        })
    
    context = {
        'game': game,
        'game_steps': game_steps_data,
        'instruction_type': 'teacher'
    }
    return render(request, 'aigames/edit_instructions_carousel.html', context)
