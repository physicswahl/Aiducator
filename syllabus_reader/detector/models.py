from django.db import models
from django.contrib.auth.models import User
from aigames.models import GameMatchup, Team


class TeamDetectorData(models.Model):
    """Store team data for the detector game"""
    matchup = models.ForeignKey(GameMatchup, on_delete=models.CASCADE, related_name='detector_data')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    # Step progress tracking
    current_step = models.IntegerField(default=1)
    step1_completed = models.BooleanField(default=False)
    step2_completed = models.BooleanField(default=False)
    step3_completed = models.BooleanField(default=False)
    step4_completed = models.BooleanField(default=False)
    
    # Game-specific data fields (to be expanded based on game requirements)
    setup_data = models.JSONField(default=dict, blank=True)  # Step 1 data
    collection_data = models.JSONField(default=dict, blank=True)  # Step 2 data
    analysis_data = models.JSONField(default=dict, blank=True)  # Step 3 data
    results_data = models.JSONField(default=dict, blank=True)  # Step 4 data
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['matchup', 'team']
        verbose_name = "Team Detector Data"
        verbose_name_plural = "Team Detector Data"
    
    def __str__(self):
        return f"{self.team.name} - Detector Game - {self.matchup.ai_game.title}"
    
    def get_completed_steps(self):
        """Return list of completed step numbers"""
        completed = []
        if self.step1_completed:
            completed.append(1)
        if self.step2_completed:
            completed.append(2)
        if self.step3_completed:
            completed.append(3)
        if self.step4_completed:
            completed.append(4)
        return completed
    
    def is_step_accessible(self, step_number):
        """Check if a step is accessible based on completion of previous steps"""
        if step_number == 1:
            return True
        elif step_number == 2:
            return self.step1_completed
        elif step_number == 3:
            return self.step2_completed
        elif step_number == 4:
            return self.step3_completed
        return False
    
    def complete_step(self, step_number):
        """Mark a step as completed"""
        if step_number == 1:
            self.step1_completed = True
        elif step_number == 2:
            self.step2_completed = True
        elif step_number == 3:
            self.step3_completed = True
        elif step_number == 4:
            self.step4_completed = True
        
        # Update current step to next available step
        if step_number < 4 and step_number >= self.current_step:
            self.current_step = step_number + 1
        
        self.save()


class DetectorSubmission(models.Model):
    """Store individual submissions or actions within the detector game"""
    team_data = models.ForeignKey(TeamDetectorData, on_delete=models.CASCADE, related_name='submissions')
    step_number = models.IntegerField()
    submission_type = models.CharField(max_length=50)  # 'setup', 'collection', 'analysis', etc.
    
    # Flexible data storage for different types of submissions
    data = models.JSONField(default=dict)
    
    # Validation/scoring
    is_validated = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    # User who made the submission
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Detector Submission"
        verbose_name_plural = "Detector Submissions"
    
    def __str__(self):
        return f"{self.team_data.team.name} - Step {self.step_number} - {self.submission_type}"
