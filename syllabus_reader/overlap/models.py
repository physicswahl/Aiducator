from django.db import models
from django.contrib.auth.models import User
from aigames.models import Team, GameMatchup


class TeamOverlapData(models.Model):
    """Stores overlap game data for each team"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    matchup = models.ForeignKey(GameMatchup, on_delete=models.CASCADE)
    
    # Step progression tracking
    current_step = models.IntegerField(default=1)
    step1_completed = models.BooleanField(default=False)
    step2_completed = models.BooleanField(default=False)
    step3_completed = models.BooleanField(default=False)
    step4_completed = models.BooleanField(default=False)
    step5_completed = models.BooleanField(default=False)
    
    # Game configuration (Step 1)
    sensitivity_level = models.IntegerField(default=50, help_text="Sensitivity level 1-100")
    threshold_value = models.FloatField(default=0.75, help_text="Detection threshold 0-1")
    overlap_mode = models.CharField(max_length=50, default='standard', 
                                  help_text="Overlap detection mode")
    
    # Data collection (Step 2)
    data_points_collected = models.IntegerField(default=0)
    baseline_established = models.BooleanField(default=False)
    collection_notes = models.TextField(blank=True)
    
    # Analysis results (Step 3)
    overlap_percentage = models.FloatField(null=True, blank=True)
    analysis_complete = models.BooleanField(default=False)
    analysis_notes = models.TextField(blank=True)
    
    # Circle placement (Step 3)
    circle_x = models.FloatField(null=True, blank=True, help_text="X position of placed circle")
    circle_y = models.FloatField(null=True, blank=True, help_text="Y position of placed circle")
    circle_placement_submitted = models.BooleanField(default=False)
    placement_notes = models.TextField(blank=True, help_text="Notes about circle placement strategy")
    
    # Final results (Step 4)
    evaluation_strategy = models.TextField(blank=True, help_text="Team's strategy for evaluating opponent's circle")
    evaluation_clicks = models.JSONField(default=list, blank=True, help_text="Stored click data as JSON")
    click_count = models.IntegerField(default=0, help_text="Number of clicks made")
    step4_submitted = models.BooleanField(default=False, help_text="Whether step 4 has been submitted for teacher validation")
    final_score = models.FloatField(null=True, blank=True)
    
    # Step 5: Final Reflection
    reflection_notes = models.TextField(blank=True, help_text="Team's final reflection on the game and strategies")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['team', 'matchup']
        
    def __str__(self):
        return f"{self.team.name} - {self.matchup.ai_game.title} - Step {self.current_step}"
    
    def get_completion_percentage(self):
        """Calculate completion percentage based on completed steps"""
        completed_steps = sum([
            self.step1_completed,
            self.step2_completed, 
            self.step3_completed,
            self.step4_completed,
            self.step5_completed
        ])
        return (completed_steps / 5) * 100
    
    def can_access_step(self, step_number):
        """Check if team can access a specific step"""
        if step_number == 1:
            return True
        elif step_number == 2:
            return self.step1_completed
        elif step_number == 3:
            return self.step2_completed
        elif step_number == 4:
            return self.step3_completed
        elif step_number == 5:
            return self.step4_completed
        return False
    
    def complete_step(self, step_number):
        """Mark a step as completed and advance to next step"""
        if step_number == 1:
            self.step1_completed = True
            self.current_step = 2
        elif step_number == 2:
            self.step2_completed = True
            self.current_step = 3
        elif step_number == 3:
            self.step3_completed = True
            self.current_step = 4
        elif step_number == 4:
            self.step4_completed = True
            self.current_step = 5
        elif step_number == 5:
            self.step5_completed = True
            # Game is now fully completed
            
        self.save()


class OverlapSubmission(models.Model):
    """Stores submission data for overlap game steps"""
    team_data = models.ForeignKey(TeamOverlapData, on_delete=models.CASCADE)
    step_number = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Submission content
    submission_data = models.JSONField(default=dict, help_text="Step-specific submission data")
    notes = models.TextField(blank=True)
    
    # Scoring
    score = models.FloatField(null=True, blank=True)
    max_score = models.FloatField(default=100)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['team_data', 'step_number', 'user']
        
    def __str__(self):
        return f"{self.team_data.team.name} - Step {self.step_number} - {self.user.username}"
    
    def get_score_percentage(self):
        """Get score as percentage"""
        if self.score is not None and self.max_score > 0:
            return (self.score / self.max_score) * 100
        return 0
