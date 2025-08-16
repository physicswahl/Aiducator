from django import forms
from django.contrib.auth.models import User
from .models import AiGame, Team, GameResource, TeamInvitation, School, GameMatchup, GameStep, InstructionStep

class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['name', 'short_name', 'description', 'logo', 'website_url', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'website_url': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AiGameForm(forms.ModelForm):
    class Meta:
        model = AiGame
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter game title...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the game...'}),
        }

class GameStepForm(forms.ModelForm):
    class Meta:
        model = GameStep
        fields = ['step_number', 'title', 'description', 'url_pattern', 'estimated_duration_minutes']
        widgets = {
            'step_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter step title...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe this step...'}),
            'url_pattern': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'app_name:view_name or /pattern/'}),
            'estimated_duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class GameResourceForm(forms.ModelForm):
    class Meta:
        model = GameResource
        fields = ['title', 'description', 'file', 'resource_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
        }

class TeamInvitationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    
    class Meta:
        model = TeamInvitation
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Optional message for the invitation...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].required = False
    
    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")

class JoinTeamForm(forms.Form):
    """Form for users to join a team for a specific game"""
    team = forms.ModelChoiceField(
        queryset=Team.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a team..."
    )
    
    def __init__(self, ai_game=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if ai_game and user and hasattr(user, 'profile'):
            # Filter teams that are already participating in this game and from the same school
            participating_teams = ai_game.participating_teams.filter(
                is_active=True, 
                school=user.profile.school
            )
            self.fields['team'].queryset = participating_teams

class GameMatchupForm(forms.ModelForm):
    """Form for teachers to create game matchups between teams"""
    class Meta:
        model = GameMatchup
        fields = ['ai_game', 'team1', 'team2', 'scheduled_date', 'notes']
        widgets = {
            'ai_game': forms.Select(attrs={'class': 'form-select'}),
            'team1': forms.Select(attrs={'class': 'form-select'}),
            'team2': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Optional notes about this matchup...'
            }),
        }
    
    def __init__(self, user=None, initial_game=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'profile'):
            # Only show teams from the user's school
            school_teams = Team.objects.filter(school=user.profile.school, is_active=True)
            self.fields['team1'].queryset = school_teams
            self.fields['team2'].queryset = school_teams
        
        # Pre-select game if provided
        if initial_game:
            self.fields['ai_game'].initial = initial_game
        
        self.fields['scheduled_date'].required = False
        self.fields['notes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        team1 = cleaned_data.get('team1')
        team2 = cleaned_data.get('team2')
        
        if team1 and team2:
            if team1 == team2:
                raise forms.ValidationError("A team cannot play against itself.")
            if team1.school != team2.school:
                raise forms.ValidationError("Teams must be from the same school.")
        
        return cleaned_data

class SchoolTeamForm(forms.ModelForm):
    """Form for creating teams within a school"""
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter team name...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Optional team description...'
            }),
        }
    
    def __init__(self, school=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        self.fields['description'].required = False
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if self.school:
            # Check if team name already exists in this school
            existing_team = Team.objects.filter(
                school=self.school, 
                name=name, 
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_team.exists():
                raise forms.ValidationError(f"A team named '{name}' already exists in your school.")
        
        return name

class TeamMemberForm(forms.Form):
    """Form for adding members to a team"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username to add...'
        }),
        help_text="Enter the username of the person you want to add to this team"
    )
    role = forms.ChoiceField(
        choices=[('member', 'Member'), ('leader', 'Leader'), ('admin', 'Admin')],
        initial='member',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the role for this team member"
    )
    
    def __init__(self, team=None, school=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = team
        self.school = school
    
    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
            
            # Check if user has a profile and belongs to the same school
            if not hasattr(user, 'profile'):
                raise forms.ValidationError("This user does not have a profile set up.")
            
            if self.school and user.profile.school != self.school:
                raise forms.ValidationError("This user does not belong to your school.")
            
            # Check if user is already a member of this team
            if self.team and self.team.members.filter(id=user.id).exists():
                raise forms.ValidationError("This user is already a member of this team.")
            
            return user
        except User.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")

class GameStepForm(forms.ModelForm):
    """Form for creating and editing game steps"""
    class Meta:
        model = GameStep
        fields = ['step_number', 'title', 'description', 'estimated_duration_minutes']
        widgets = {
            'step_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Step title...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'What happens in this step...'}),
            'estimated_duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '10'}),
        }

    def __init__(self, ai_game=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if ai_game and not self.instance.pk:
            # Set default step number to next available
            existing_steps = ai_game.steps.count()
            self.fields['step_number'].initial = existing_steps + 1

class InstructionStepForm(forms.ModelForm):
    """Form for creating and editing instruction steps"""
    class Meta:
        model = InstructionStep
        fields = ['title', 'content', 'role']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Instruction title...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed instruction content...'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
