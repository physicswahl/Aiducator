from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class School(models.Model):
    """Schools that users belong to"""
    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=50, help_text="Short name or abbreviation")
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True, help_text="School logo for white-labeling")
    navbar_color = models.CharField(max_length=7, blank=True, help_text="Navbar color in hex format (e.g., #2E2B86)")
    primary_button_color = models.CharField(max_length=7, blank=True, help_text="Primary button color in hex format (e.g., #2E2B86)")
    website_url = models.URLField(blank=True, help_text="School website URL")
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def logo_url(self):
        """Get logo URL or return default if no logo"""
        if self.logo:
            return self.logo.url
        return None
    
    class Meta:
        ordering = ['name']

class UserProfile(models.Model):
    """Extended user profile with role-based permissions"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'), 
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    @property
    def can_create_teams(self):
        """Teachers and Admins can create teams"""
        return self.role in ['teacher', 'admin']
    
    @property
    def can_create_games(self):
        """Only Admins can create games"""
        return self.role == 'admin'
    
    @property
    def can_modify_syllabus(self):
        """Only Admins can modify syllabus, units, and associate games"""
        return self.role == 'admin'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_admin(self):
        return self.role == 'admin'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile when a User is created"""
    if created:
        # Get the first active school as default
        default_school = School.objects.filter(is_active=True).first()
        if not default_school:
            # If no active schools, create one
            default_school = School.objects.create(
                name="Default School",
                short_name="Default",
                description="Default school for new users"
            )
        UserProfile.objects.create(user=instance, school=default_school)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

class AiGame(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    @property
    def has_multiple_steps(self):
        """Check if this game has multiple steps by counting active steps"""
        return self.steps.filter(is_active=True).count() > 1
    
    def get_ordered_steps(self):
        """Get all active game steps for this game ordered by step number"""
        return self.steps.filter(is_active=True).order_by('step_number')
    
    def get_total_estimated_duration(self):
        """Get total estimated duration for all game steps in minutes"""
        total = self.steps.filter(is_active=True).aggregate(
            total_minutes=models.Sum('estimated_duration_minutes')
        )['total_minutes']
        return total or 0
    
    def get_step_by_number(self, step_number):
        """Get a specific game step by number"""
        return self.steps.filter(
            step_number=step_number, 
            is_active=True
        ).first()
    
    def get_instructions_for_step_and_role(self, step_number, user_role):
        """Get instruction chain for a specific step number and role"""
        game_step = self.get_step_by_number(step_number)
        if not game_step:
            return []
        return game_step.get_instruction_chain_for_role(user_role)
    
    def get_teams_count(self):
        """Get count of unique teams involved in this game through matchups"""
        team1_ids = set(self.matchups.values_list('team1_id', flat=True))
        team2_ids = set(self.matchups.values_list('team2_id', flat=True))
        return len(team1_ids.union(team2_ids))
    
    def get_first_step_url(self, matchup_id=None):
        """Get the URL for the first step of this game"""
        first_step = self.get_step_by_number(1)
        if first_step:
            url = first_step.get_url(matchup_id)
            return url
        return None

    class Meta:
        ordering = ['title']

class GameStep(models.Model):
    """Individual steps within a multi-step AI game"""
    ai_game = models.ForeignKey(AiGame, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField(help_text="Sequential step number (1, 2, 3...)")
    title = models.CharField(max_length=255, help_text="Title of this step")
    description = models.TextField(blank=True, help_text="Brief description of what happens in this step")
    url_pattern = models.CharField(max_length=500, default='placeholder:step', help_text="URL pattern for this step (e.g., 'phoneme_density:step1_analysis')")
    estimated_duration_minutes = models.PositiveIntegerField(default=1, help_text="Estimated time to complete this step in minutes")
    requires_validation = models.BooleanField(default=False, help_text="Whether this step requires teacher validation before students can proceed")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.ai_game.title} - Step {self.step_number}: {self.title}"
    
    def get_url(self, matchup_id):
        """Generate the actual URL for this step with the given matchup ID"""
        if not matchup_id:
            return None
        
        # For URL patterns like 'phoneme_density:step1_analysis', we need to construct the URL
        # This will be handled by the specific game implementation's URL resolver
        from django.urls import reverse, NoReverseMatch
        try:
            # Try to reverse the URL pattern with the matchup_id
            url = reverse(self.url_pattern, kwargs={'matchup_id': matchup_id})
            return url
        except NoReverseMatch as e:
            # Fallback: construct a simple URL pattern
            app_name = self.url_pattern.split(':')[0] if ':' in self.url_pattern else ''
            view_name = self.url_pattern.split(':')[1] if ':' in self.url_pattern else self.url_pattern
            fallback_url = f"/{app_name}/{matchup_id}/{view_name}/" if app_name else f"/{matchup_id}/{view_name}/"
            return fallback_url
    
    def get_instruction_chain_for_role(self, role):
        """Get the linked chain of instructions for a specific role in this step"""
        # Find the first instruction (one with no incoming links)
        first_instruction = self.instruction_steps.filter(
            role=role,
            previous_instruction__isnull=True,
            is_active=True
        ).first()
        
        if not first_instruction:
            return []
        
        # Build the chain by following links
        chain = []
        current = first_instruction
        while current:
            chain.append(current)
            current = current.next_instruction
            if current and current.id in [inst.id for inst in chain]:  # Prevent infinite loops
                break
        
        return chain
    
    def get_instructions_for_user(self, user):
        """Get the appropriate instruction chain based on user role"""
        if hasattr(user, 'profile'):
            if user.profile.is_teacher or user.profile.is_admin:
                return self.get_instruction_chain_for_role('teacher')
            else:
                return self.get_instruction_chain_for_role('student')
        # Default to student instructions
        return self.get_instruction_chain_for_role('student')
    
    class Meta:
        ordering = ['ai_game', 'step_number']
        unique_together = ['ai_game', 'step_number']

class InstructionStep(models.Model):
    """Individual instruction steps that can be chained together within a GameStep"""
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    
    game_step = models.ForeignKey(GameStep, on_delete=models.CASCADE, related_name='instruction_steps')
    title = models.CharField(max_length=255, help_text="Title of this instruction")
    content = models.TextField(help_text="The instruction content")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, 
                           help_text="Which role this instruction is for (student or teacher)")
    
    # Linked list structure for chaining instructions within a step
    next_instruction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='previous_instruction',
                                       help_text="Next instruction in the sequence")
    
    is_active = models.BooleanField(default=True, help_text="Whether this instruction is currently visible")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_instruction_steps')
    
    class Meta:
        ordering = ['game_step', 'role', 'id']  # Order by game step, role, then creation order
    
    def __str__(self):
        return f"{self.game_step.ai_game.title} - Step {self.game_step.step_number}: {self.title} ({self.get_role_display()})"
    
    def is_visible_to_user(self, user):
        """Check if this instruction should be visible to the given user"""
        if not hasattr(user, 'profile'):
            return self.role == 'student'  # Default to student view
        
        user_role = user.profile.role
        if self.role == 'student':
            return user_role == 'student'
        elif self.role == 'teacher':
            return user_role in ['teacher', 'admin']
        
        return False
    
    def get_position_in_chain(self):
        """Get the position of this instruction in the chain (1-based)"""
        chain = self.game_step.get_instruction_chain_for_role(self.role)
        try:
            return chain.index(self) + 1
        except ValueError:
            return None  # Not in main chain (orphaned)
    
    def is_orphaned(self):
        """Check if this instruction has no incoming links and is not the first"""
        has_incoming = self.previous_instruction.exists()
        is_first = not InstructionStep.objects.filter(
            game_step=self.game_step,
            role=self.role,
            previous_instruction__isnull=True,
            is_active=True
        ).exclude(id=self.id).exists()
        
        return not has_incoming and not is_first
    
    def get_feedback_summary(self):
        """Get summary of thumbs up/down feedback for this instruction"""
        total_feedback = self.feedback.count()
        if total_feedback == 0:
            return {'total': 0, 'thumbs_up': 0, 'thumbs_down': 0, 'percentage_positive': 0}
        
        thumbs_up = self.feedback.filter(is_helpful=True).count()
        thumbs_down = self.feedback.filter(is_helpful=False).count()
        percentage_positive = round((thumbs_up / total_feedback) * 100, 1) if total_feedback > 0 else 0
        
        return {
            'total': total_feedback,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'percentage_positive': percentage_positive
        }
    
    def is_problematic(self):
        """Check if this instruction has problematic feedback patterns"""
        summary = self.get_feedback_summary()
        
        # Consider problematic if:
        # 1. More than 5 pieces of feedback and less than 60% positive
        # 2. More than 10 pieces of feedback and less than 70% positive
        if summary['total'] >= 10:
            return summary['percentage_positive'] < 70
        elif summary['total'] >= 5:
            return summary['percentage_positive'] < 60
        
        return False
    
    def has_recent_negative_feedback(self, days=7):
        """Check if instruction has received negative feedback in recent days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.feedback.filter(
            is_helpful=False,
            created_at__gte=cutoff_date
        ).exists()
    
    def get_problematic_reasons(self):
        """Get list of reasons why this instruction is considered problematic"""
        reasons = []
        summary = self.get_feedback_summary()
        
        if summary['total'] >= 10 and summary['percentage_positive'] < 70:
            reasons.append(f"Low satisfaction: {summary['percentage_positive']}% positive from {summary['total']} reviews")
        elif summary['total'] >= 5 and summary['percentage_positive'] < 60:
            reasons.append(f"Very low satisfaction: {summary['percentage_positive']}% positive from {summary['total']} reviews")
        
        if self.has_recent_negative_feedback():
            reasons.append("Recent negative feedback (last 7 days)")
            
        return reasons

class InstructionStepFeedback(models.Model):
    """User feedback on instruction steps (thumbs up/down)"""
    instruction_step = models.ForeignKey(InstructionStep, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instruction_feedback')
    is_helpful = models.BooleanField(help_text="True for thumbs up, False for thumbs down")
    feedback_comment = models.TextField(blank=True, help_text="Optional comment explaining the feedback")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        feedback_type = "👍" if self.is_helpful else "👎"
        return f"{self.user.username} - {self.instruction_step.title}: {feedback_type}"
    
    class Meta:
        unique_together = ['instruction_step', 'user']  # One feedback per user per instruction
        ordering = ['-created_at']

class Team(models.Model):
    """Teams - groups of users that can participate in multiple AI games"""
    name = models.CharField(max_length=255)  # Team names unique per school
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teams')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    members = models.ManyToManyField(User, through='TeamMembership', related_name='teams')
    games = models.ManyToManyField(AiGame, through='TeamGameParticipation', related_name='participating_teams')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_current_step_url(self, ai_game):
        """Get the URL for the current (next uncompleted) step for this team
        This method now looks for active matchups for this team and game"""
        # Find an active matchup for this team and game
        from django.db.models import Q
        matchup = GameMatchup.objects.filter(
            Q(team1=self) | Q(team2=self),
            ai_game=ai_game,
            status__in=['scheduled', 'in_progress']
        ).first()
        
        if matchup:
            return matchup.get_current_step_url()
        
        # Fallback to the first step URL if no matchup found
        return ai_game.get_first_step_url()

    class Meta:
        ordering = ['name']
        unique_together = ['school', 'name']  # Team names must be unique within each school

class TeamMembership(models.Model):
    """Through model for Team-User relationship with roles"""
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('leader', 'Leader'),
        ('admin', 'Admin'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"
    
    class Meta:
        unique_together = ['team', 'user']  # User can only be in a team once

class TeamGameParticipation(models.Model):
    """Through model for Team-AiGame relationship - tracks which teams participate in which games"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    ai_game = models.ForeignKey(AiGame, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.team.name} participating in {self.ai_game.title}"
    
    class Meta:
        unique_together = ['team', 'ai_game']  # Team can only participate in a game once

class GameMatchup(models.Model):
    """Pairs teams together to play games - only visible to teachers in the same school"""
    MATCHUP_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ai_game = models.ForeignKey(AiGame, on_delete=models.CASCADE, related_name='matchups')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matchups_as_team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matchups_as_team2')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='game_matchups')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_matchups')
    status = models.CharField(max_length=20, choices=MATCHUP_STATUS_CHOICES, default='scheduled')
    scheduled_date = models.DateTimeField(null=True, blank=True, help_text="When the game is scheduled to be played")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Teacher notes about this matchup")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.ai_game.title}: {self.team1.name} vs {self.team2.name}"
    
    def clean(self):
        """Validate that both teams belong to the same school"""
        from django.core.exceptions import ValidationError
        if self.team1.school != self.team2.school:
            raise ValidationError("Teams must be from the same school")
        if self.team1 == self.team2:
            raise ValidationError("A team cannot play against itself")
        # Set school to the teams' school
        if self.team1.school:
            self.school = self.team1.school
    
    def get_teams(self):
        """Get both teams as a list"""
        return [self.team1, self.team2]
    
    def get_other_team(self, team):
        """Get the other team in the matchup"""
        if team == self.team1:
            return self.team2
        elif team == self.team2:
            return self.team1
        return None
    
    @property
    def duration_minutes(self):
        """Calculate matchup duration in minutes"""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None
    
    def get_current_step(self):
        """Get the current (next uncompleted) step for this matchup"""
        # Get the latest completed step
        completed_steps = self.step_progress.filter(
            is_completed=True
        ).order_by('-game_step__step_number')
        
        if completed_steps.exists():
            last_completed = completed_steps.first().game_step.step_number
            # Return the next step
            next_step = self.ai_game.get_step_by_number(last_completed + 1)
            return next_step
        else:
            # Return the first step if none completed
            return self.ai_game.get_step_by_number(1)
    
    def get_current_step_url(self):
        """Get the URL for the current (next uncompleted) step for this matchup"""
        current_step = self.get_current_step()
        if current_step:
            return current_step.get_url(self.id)
        return None
    
    def get_progress_for_step(self, step_number):
        """Get progress for a specific step"""
        game_step = self.ai_game.get_step_by_number(step_number)
        if game_step:
            return self.step_progress.filter(game_step=game_step).first()
        return None
    
    def complete_step(self, step_number, completed_by=None):
        """Mark a step as completed for this matchup"""
        game_step = self.ai_game.get_step_by_number(step_number)
        if game_step:
            progress, created = MatchupStepProgress.objects.get_or_create(
                matchup=self,
                game_step=game_step,
                defaults={
                    'is_completed': True, 
                    'completed_at': timezone.now(),
                    'completed_by': completed_by
                }
            )
            if not created and not progress.is_completed:
                progress.complete_step()
                if completed_by:
                    progress.completed_by = completed_by
                    progress.save()
            return progress
        return None
    
    def get_last_activity(self):
        """Get the most recent activity for this matchup"""
        activities = []
        
        # Add matchup status changes
        if self.completed_at:
            activities.append({
                'datetime': self.completed_at,
                'activity': 'Matchup completed',
                'actor': f'Teacher ({self.created_by.get_full_name() or self.created_by.username})'
            })
        
        if self.started_at:
            activities.append({
                'datetime': self.started_at,
                'activity': 'Matchup started',
                'actor': f'Teacher ({self.created_by.get_full_name() or self.created_by.username})'
            })
        
        # Add step completions
        for progress in self.step_progress.filter(is_completed=True):
            game_step = progress.game_step
            if game_step.requires_validation:
                # Validation-required steps are completed by the teacher
                activities.append({
                    'datetime': progress.completed_at,
                    'activity': f'Step {progress.game_step.step_number} validated',
                    'actor': f'Teacher ({self.created_by.get_full_name() or self.created_by.username})'
                })
            else:
                # Regular steps are completed by student teams
                activities.append({
                    'datetime': progress.completed_at,
                    'activity': f'Step {progress.game_step.step_number} completed',
                    'actor': f'Teams ({self.team1.name} & {self.team2.name})'
                })
        
        # Add creation as fallback
        activities.append({
            'datetime': self.created_at,
            'activity': 'Matchup created',
            'actor': f'Teacher ({self.created_by.get_full_name() or self.created_by.username})'
        })
        
        # Sort by datetime and return the most recent
        if activities:
            activities.sort(key=lambda x: x['datetime'], reverse=True)
            return activities[0]
        
        return None

    def is_team_validated_for_step(self, team, step_number):
        """Check if a specific team has been validated for a specific step"""
        game_step = self.ai_game.get_step_by_number(step_number)
        if not game_step:
            return False
        
        validation = TeamStepValidation.objects.filter(
            matchup=self,
            team=team,
            game_step=game_step,
            is_validated=True
        ).first()
        
        return validation is not None
    
    def get_team_validation_for_step(self, team, step_number):
        """Get the validation record for a specific team and step"""
        game_step = self.ai_game.get_step_by_number(step_number)
        if not game_step:
            return None
        
        return TeamStepValidation.objects.filter(
            matchup=self,
            team=team,
            game_step=game_step
        ).first()

    class Meta:
        ordering = ['-created_at']
        # Removed unique_together constraint to allow new matchups when previous ones are cancelled

class GameResource(models.Model):
    """Resources uploaded by team members for their team in a specific game"""
    RESOURCE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('data', 'Data File'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='game_resources/%Y/%m/%d/')
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES, default='document')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='resources')
    ai_game = models.ForeignKey(AiGame, on_delete=models.CASCADE, related_name='game_resources')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resources')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (by {self.uploaded_by.username} for {self.team.name} in {self.ai_game.title})"

    class Meta:
        ordering = ['-created_at']

class TeamInvitation(models.Model):
    """Invitations to join teams"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    ai_game = models.ForeignKey(AiGame, on_delete=models.CASCADE, null=True, blank=True, 
                               help_text="Optional: specific game the invitation is for")
    message = models.TextField(blank=True)
    accepted = models.BooleanField(null=True, blank=True)  # None=pending, True=accepted, False=declined
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "Pending" if self.accepted is None else ("Accepted" if self.accepted else "Declined")
        game_info = f" for {self.ai_game.title}" if self.ai_game else ""
        return f"{self.invited_user.username} → {self.team.name}{game_info} ({status})"

    class Meta:
        unique_together = ['team', 'invited_user', 'ai_game']  # Can't invite same user to same team for same game twice
        ordering = ['-created_at']

class MatchupStepProgress(models.Model):
    """Tracks step completion for each matchup (game instance) rather than individual teams"""
    matchup = models.ForeignKey(GameMatchup, on_delete=models.CASCADE, related_name='step_progress')
    game_step = models.ForeignKey(GameStep, on_delete=models.CASCADE, related_name='matchup_progress')
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Notes about progress on this step for this matchup")
    
    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.matchup} - Step {self.game_step.step_number} ({status})"
    
    @property
    def duration_minutes(self):
        """Calculate how long this step took"""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None
    
    def complete_step(self):
        """Mark this step as completed"""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()
    
    class Meta:
        unique_together = ['matchup', 'game_step']  # One progress record per step per matchup
        ordering = ['matchup', 'game_step__step_number']


class TeamStepValidation(models.Model):
    """Tracks teacher validation for each team's work on validation-required steps"""
    matchup = models.ForeignKey(GameMatchup, on_delete=models.CASCADE, related_name='team_validations')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='step_validations')
    game_step = models.ForeignKey(GameStep, on_delete=models.CASCADE, related_name='team_validations')
    is_validated = models.BooleanField(default=False)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Teacher who validated this team's work")
    validated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Teacher notes about this team's work")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def validate(self, teacher):
        """Mark this team's work as validated by the teacher"""
        self.is_validated = True
        self.validated_by = teacher
        self.validated_at = timezone.now()
        self.save()
        
        # Check if both teams are now validated and complete the step if so
        other_team = self.matchup.team2 if self.team == self.matchup.team1 else self.matchup.team1
        other_validation, _ = TeamStepValidation.objects.get_or_create(
            matchup=self.matchup,
            team=other_team,
            game_step=self.game_step
        )
        
        if other_validation.is_validated:
            # Both teams validated - complete the step
            self.matchup.complete_step(self.game_step.step_number)
    
    def __str__(self):
        status = "Validated" if self.is_validated else "Pending"
        return f"{self.team.name} - Step {self.game_step.step_number} ({status})"
    
    class Meta:
        unique_together = ['matchup', 'team', 'game_step']  # One validation record per team per step per matchup
        ordering = ['matchup', 'game_step__step_number', 'team__name']

