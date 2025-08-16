from .models import UserProfile, School

def user_profile(request):
    """Add user profile and school information to template context"""
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist with default school
            default_school = School.objects.filter(is_active=True).first()
            if not default_school:
                default_school = School.objects.create(
                    name="Default School",
                    short_name="Default",
                    description="Default school for users"
                )
            profile = UserProfile.objects.create(user=request.user, role='student', school=default_school)
        
        # Get school information for white-labeling (school is now required)
        school = profile.school
        school_logo = school.logo_url
        school_name = school.name
        navbar_color = school.navbar_color if school.navbar_color else None
        primary_button_color = school.primary_button_color if school.primary_button_color else None
        
        return {
            'user_profile': profile,
            'user_role': profile.role,
            'user_school': school,
            'school_logo': school_logo,
            'school_name': school_name,
            'navbar_color': navbar_color,
            'primary_button_color': primary_button_color,
            'can_create_teams': profile.can_create_teams,
            'can_create_games': profile.can_create_games,
            'can_modify_syllabus': profile.can_modify_syllabus,
        }
    
    return {
        'user_profile': None,
        'user_role': 'guest',
        'user_school': None,
        'school_logo': None,
        'school_name': None,
        'navbar_color': None,
        'primary_button_color': None,
        'can_create_teams': False,
        'can_create_games': False,
        'can_modify_syllabus': False,
    }
