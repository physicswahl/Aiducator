from django.contrib import admin
from .models import TeamOverlapData, OverlapSubmission


@admin.register(TeamOverlapData)
class TeamOverlapDataAdmin(admin.ModelAdmin):
    list_display = ('team', 'matchup', 'current_step', 'step4_submitted', 'final_score', 'created_at')
    list_filter = ('current_step', 'step4_submitted', 'step1_completed', 'step2_completed', 'step3_completed', 'step4_completed', 'step5_completed')
    search_fields = ('team__name', 'matchup__ai_game__title')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('team', 'matchup', 'current_step')
        }),
        ('Step Progress', {
            'fields': ('step1_completed', 'step2_completed', 'step3_completed', 'step4_completed', 'step5_completed', 'step4_submitted')
        }),
        ('Game Configuration', {
            'fields': ('sensitivity_level', 'threshold_value', 'overlap_mode')
        }),
        ('Data Collection', {
            'fields': ('data_points_collected', 'baseline_established', 'collection_notes')
        }),
        ('Analysis Results', {
            'fields': ('overlap_percentage', 'analysis_complete', 'analysis_notes')
        }),
        ('Final Results', {
            'fields': ('final_score',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('team', 'matchup__ai_game')


@admin.register(OverlapSubmission)
class OverlapSubmissionAdmin(admin.ModelAdmin):
    list_display = ('team_data', 'step_number', 'user', 'score', 'submitted_at')
    list_filter = ('step_number', 'submitted_at', 'graded_at')
    search_fields = ('team_data__team__name', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('submitted_at', 'graded_at')
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('team_data', 'step_number', 'user')
        }),
        ('Content', {
            'fields': ('submission_data', 'notes')
        }),
        ('Scoring', {
            'fields': ('score', 'max_score')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'graded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('team_data__team', 'user')
