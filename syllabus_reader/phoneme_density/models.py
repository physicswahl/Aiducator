from django.db import models
from django.contrib.auth.models import User
from aigames.models import GameMatchup, Team


class TeamStep4Data(models.Model):
    """Store team data for Step 4 - text creation"""
    matchup = models.ForeignKey(GameMatchup, on_delete=models.CASCADE, related_name='step4_data')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    selected_phoneme = models.CharField(max_length=10, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['matchup', 'team']
    
    def __str__(self):
        return f"{self.team.name} - Step 4 - {self.matchup.ai_game.title}"


class TeamText(models.Model):
    """Individual text created by a team in Step 4"""
    APPROVAL_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Needs Revision'),
    ]
    
    step4_data = models.ForeignKey(TeamStep4Data, on_delete=models.CASCADE, related_name='texts')
    text_number = models.IntegerField()  # 1-8
    content = models.TextField(blank=True)
    
    # Approval workflow
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    teacher_feedback = models.TextField(blank=True)
    
    # Phoneme analysis (calculated automatically)
    phoneme_count = models.IntegerField(default=0)
    total_characters = models.IntegerField(default=0)  # excluding spaces
    phoneme_density = models.FloatField(default=0.0)  # percentage
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['step4_data', 'text_number']
        ordering = ['text_number']
    
    def calculate_phoneme_stats(self):
        """Calculate phoneme statistics for this text"""
        if not self.content or not self.step4_data.selected_phoneme:
            self.phoneme_count = 0
            self.total_characters = 0
            self.phoneme_density = 0.0
            return
        
        text_lower = self.content.lower()
        phoneme_lower = self.step4_data.selected_phoneme.lower()
        
        # Count phoneme occurrences
        self.phoneme_count = text_lower.count(phoneme_lower)
        
        # Count total characters excluding spaces
        self.total_characters = len(text_lower.replace(' ', ''))
        
        # Calculate density percentage
        if self.total_characters > 0:
            self.phoneme_density = (self.phoneme_count / self.total_characters) * 100
        else:
            self.phoneme_density = 0.0
    
    def save(self, *args, **kwargs):
        """Override save to automatically calculate phoneme stats"""
        self.calculate_phoneme_stats()
        super().save(*args, **kwargs)
    
    def get_density_category(self):
        """Return density category for display purposes"""
        if self.phoneme_density >= 8:
            return 'high'
        elif self.phoneme_density >= 4:
            return 'medium'
        else:
            return 'low'
    
    def __str__(self):
        return f"{self.step4_data.team.name} - Text {self.text_number}"


class PhonemeGuess(models.Model):
    """Store team's guess about opponent's phoneme in Step 5"""
    matchup = models.ForeignKey(GameMatchup, on_delete=models.CASCADE, related_name='phoneme_guesses')
    guessing_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='phoneme_guesses_made')
    target_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='phoneme_guesses_received')
    
    # Guesses
    phoneme_guess = models.CharField(max_length=10, blank=True, null=True)
    rule_description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['matchup', 'guessing_team', 'target_team']
    
    def __str__(self):
        return f"{self.guessing_team.name} guessing {self.target_team.name}'s phoneme"


class TextGuess(models.Model):
    """Store which texts the team thinks follow the phoneme rule"""
    phoneme_guess = models.ForeignKey(PhonemeGuess, on_delete=models.CASCADE, related_name='text_guesses')
    text_number = models.IntegerField()  # 1-8, which text from opponent
    follows_rule = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['phoneme_guess', 'text_number']
        ordering = ['text_number']
    
    def __str__(self):
        return f"{self.phoneme_guess.guessing_team.name} - Text {self.text_number}: {self.follows_rule}"
