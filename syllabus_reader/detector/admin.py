from django.contrib import admin
from .models import TeamDetectorData, DetectorSubmission


@admin.register(TeamDetectorData)
class TeamDetectorDataAdmin(admin.ModelAdmin):
    list_display = ('team', 'matchup', 'current_step', 'created_at', 'updated_at')
    list_filter = ('current_step', 'step1_completed', 'step2_completed', 'step3_completed', 'step4_completed', 'created_at')
    search_fields = ('team__name', 'matchup__ai_game__title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('matchup', 'team')
        }),
        ('Progress Tracking', {
            'fields': ('current_step', 'step1_completed', 'step2_completed', 'step3_completed', 'step4_completed')
        }),
        ('Game Data', {
            'fields': ('setup_data', 'collection_data', 'analysis_data', 'results_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_completed_steps_display(self, obj):
        completed = obj.get_completed_steps()
        return f"{len(completed)}/4 steps completed"
    get_completed_steps_display.short_description = "Progress"


@admin.register(DetectorSubmission)
class DetectorSubmissionAdmin(admin.ModelAdmin):
    list_display = ('team_data', 'step_number', 'submission_type', 'is_validated', 'score', 'submitted_by', 'created_at')
    list_filter = ('step_number', 'submission_type', 'is_validated', 'created_at')
    search_fields = ('team_data__team__name', 'submission_type', 'submitted_by__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('team_data', 'step_number', 'submission_type', 'submitted_by')
        }),
        ('Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('is_validated', 'score', 'feedback')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
