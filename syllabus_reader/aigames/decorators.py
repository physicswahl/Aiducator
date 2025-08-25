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
    4. Allows the view to proceed with the team's data
    """
    @wraps(view_func)
    def wrapper(request, matchup_id, *args, **kwargs):
        print(f"[DEBUG] teacher_can_view_team decorator called for matchup {matchup_id}")
        print(f"[DEBUG] Request GET params: {request.GET}")
        print(f"[DEBUG] User: {request.user}")
        
        matchup = get_object_or_404(GameMatchup, id=matchup_id)
        
        # Debug user profile details
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            print(f"[DEBUG] User has profile: {profile}")
            print(f"[DEBUG] Profile role: {profile.role}")
            print(f"[DEBUG] Profile school: {profile.school}")
            print(f"[DEBUG] Matchup school: {matchup.school}")
        else:
            print(f"[DEBUG] User has NO profile!")
        
        # Check if teacher is trying to view a specific team's work
        teacher_viewing_team_id = request.GET.get('team')
        print(f"[DEBUG] teacher_viewing_team_id: {teacher_viewing_team_id}")
        
        if teacher_viewing_team_id:
            print(f"[DEBUG] Teacher viewing mode detected for team {teacher_viewing_team_id}")
            # Verify user is a teacher for this game's school
            if (hasattr(request.user, 'profile') and 
                request.user.profile.role == 'teacher' and 
                request.user.profile.school == matchup.school):
                
                print(f"[DEBUG] Teacher permissions verified")
                viewing_team = get_object_or_404(Team, id=teacher_viewing_team_id)
                print(f"[DEBUG] Viewing team: {viewing_team}")
                
                # Verify this team is part of the matchup
                if viewing_team not in [matchup.team1, matchup.team2]:
                    print(f"[DEBUG] Invalid team access - team not in matchup")
                    messages.error(request, "Invalid team access.")
                    return HttpResponseRedirect(reverse('aigames:game_matchup_detail', 
                                                      kwargs={'matchup_id': matchup_id}))
                
                # Set up teacher viewing context
                request.teacher_viewing_mode = True
                request.viewing_team = viewing_team
                request.is_teacher_viewing = True
                print(f"[DEBUG] Teacher viewing context set up successfully")
                
            else:
                print(f"[DEBUG] Teacher permission denied")
                if hasattr(request.user, 'profile'):
                    print(f"[DEBUG] User role: {request.user.profile.role}")
                    print(f"[DEBUG] User school: {request.user.profile.school}")
                    print(f"[DEBUG] Matchup school: {matchup.school}")
                else:
                    print(f"[DEBUG] User has no profile")
                messages.error(request, "You don't have permission to view team data.")
                return HttpResponseRedirect(reverse('aigames:game_matchup_detail', 
                                                  kwargs={'matchup_id': matchup_id}))
        else:
            print(f"[DEBUG] Regular student access mode")
            # Regular student access - will be handled by the view
            request.teacher_viewing_mode = False
            request.viewing_team = None
            request.is_teacher_viewing = False
        
        print(f"[DEBUG] Calling original view function: {view_func.__name__}")
        # Call the original view
        return view_func(request, matchup_id, *args, **kwargs)
    
    return wrapper


def get_user_team_or_viewing_team(request, matchup):
    """
    Helper function to get the appropriate team for the current request.
    
    If teacher is viewing a specific team, returns that team.
    If student is accessing, returns their team.
    """
    print(f"[DEBUG] get_user_team_or_viewing_team called")
    print(f"[DEBUG] hasattr teacher_viewing_mode: {hasattr(request, 'teacher_viewing_mode')}")
    
    if hasattr(request, 'teacher_viewing_mode') and request.teacher_viewing_mode:
        print(f"[DEBUG] Teacher viewing mode - returning viewing_team: {request.viewing_team}")
        return request.viewing_team
    
    # Regular student access - find their team
    print(f"[DEBUG] Student access mode - finding user's team for user: {request.user}")
    user_team = (Team.objects.filter(members=request.user, matchups_as_team1=matchup).first() or 
                 Team.objects.filter(members=request.user, matchups_as_team2=matchup).first())
    
    print(f"[DEBUG] Found user team: {user_team}")
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
