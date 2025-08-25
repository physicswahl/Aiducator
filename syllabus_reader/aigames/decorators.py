"""
Decorators and utilities for handling teacher viewing mode in AI games
"""
from functools import wraps
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import GameMatchup, Team


def teacher_can_view_team(view_func):
    """
    Decorator that handles teacher viewing mode for game steps.
    
    When a teacher views a team's work, this decorator:
    1. Checks if there's a 'team' parameter in the request
    2. Verifies the teacher has permission to view that team's work
    3. Sets up the request context for team-specific viewing
    4. For non-validation steps, allows teacher viewing without team parameter
    5. Allows the view to proceed with the appropriate data
    """
    @wraps(view_func)
    def wrapper(request, matchup_id, *args, **kwargs):
        matchup = get_object_or_404(GameMatchup, id=matchup_id)
        
        # Check permissions - only allow:
        # 1. The teacher who created the matchup
        # 2. Students who are members of the teams in the matchup
        user_can_access = False
        is_teacher = False
        
        if hasattr(request.user, 'profile'):
            # Check if user is the teacher who created the matchup
            if (request.user.profile.role in ['teacher', 'admin'] and 
                matchup.created_by == request.user):
                user_can_access = True
                is_teacher = True
            
            # Check if user is a student in one of the teams
            elif request.user.profile.role == 'student':
                user_teams = request.user.teams.all()  # Fixed: use teams directly, not profile.teams
                if matchup.team1 in user_teams or matchup.team2 in user_teams:
                    user_can_access = True
                    is_teacher = False
        
        if not user_can_access:
            messages.error(request, "You don't have permission to access this matchup.")
            return HttpResponseRedirect(reverse('aigames:game_matchups_list'))
        
        # Check if teacher is trying to view a specific team's work
        teacher_viewing_team_id = request.GET.get('team')
        
        if teacher_viewing_team_id:
            # Verify user is a teacher for this game's school
            if is_teacher:
                viewing_team = get_object_or_404(Team, id=teacher_viewing_team_id)
                
                # Verify this team is part of the matchup
                if viewing_team not in [matchup.team1, matchup.team2]:
                    messages.error(request, "Invalid team access.")
                    return HttpResponseRedirect(reverse('aigames:game_matchup_detail', 
                                                      kwargs={'matchup_id': matchup_id}))
                
                # Set up teacher viewing context
                request.teacher_viewing_mode = True
                request.viewing_team = viewing_team
                request.is_teacher_viewing = True
                
            else:
                messages.error(request, "You don't have permission to view team data.")
                return HttpResponseRedirect(reverse('aigames:game_matchup_detail', 
                                                  kwargs={'matchup_id': matchup_id}))
        elif is_teacher:
            # Teacher accessing without team parameter (for non-validation steps)
            request.teacher_viewing_mode = True
            request.viewing_team = None  # No specific team
            request.is_teacher_viewing = True
        else:
            # Regular student access - will be handled by the view
            request.teacher_viewing_mode = False
            request.viewing_team = None
            request.is_teacher_viewing = False
        
        # Call the original view
        return view_func(request, matchup_id, *args, **kwargs)
    
    return wrapper


def get_user_team_or_viewing_team(request, matchup):
    """
    Helper function to get the appropriate team for the current request.
    
    If teacher is viewing a specific team, returns that team.
    If teacher is viewing general content (non-validation steps), returns None.
    If student is accessing, returns their team.
    """
    if hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode:
        if request.viewing_team:
            return request.viewing_team
        else:
            return None  # Teacher viewing general content (non-validation steps)
    
    # Regular student access - find their team
    user_team = (Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or 
                 Team.objects.filter(members=request.user, matchups_as_team2=matchup).first())
    
    return user_team


def is_teacher_viewing(request):
    """
    Check if the current request is from a teacher viewing team work
    """
    return getattr(request, 'teacher_viewing_mode', False)


def should_allow_form_submission(request):
    """
    Check if form submissions should be allowed (only for students, not teachers viewing)
    """
    return not is_teacher_viewing(request)
