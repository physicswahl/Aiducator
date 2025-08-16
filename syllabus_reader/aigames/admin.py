from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.db import transaction
from django.contrib.admin import SimpleListFilter
from .models import (AiGame, Team, TeamMembership, TeamGameParticipation, GameResource, TeamInvitation,
                     UserProfile, School, GameMatchup, GameStep, InstructionStep, 
                     InstructionStepFeedback)

class ProblematicStepFilter(SimpleListFilter):
    title = 'feedback status'
    parameter_name = 'feedback_status'

    def lookups(self, request, model_admin):
        return (
            ('problematic', 'Problematic Steps'),
            ('recent_issues', 'Recent Negative Feedback'),
            ('good', 'Good Performance'),
            ('no_feedback', 'No Feedback Yet'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'problematic':
            # Filter steps that are problematic
            problematic_ids = []
            for step in queryset:
                if step.is_problematic():
                    problematic_ids.append(step.id)
            return queryset.filter(id__in=problematic_ids)
        
        elif self.value() == 'recent_issues':
            # Filter steps with recent negative feedback
            recent_issue_ids = []
            for step in queryset:
                if step.has_recent_negative_feedback():
                    recent_issue_ids.append(step.id)
            return queryset.filter(id__in=recent_issue_ids)
        
        elif self.value() == 'good':
            # Filter steps that are performing well
            good_ids = []
            for step in queryset:
                summary = step.get_feedback_summary()
                if summary['total'] > 0 and not step.is_problematic() and not step.has_recent_negative_feedback():
                    good_ids.append(step.id)
            return queryset.filter(id__in=good_ids)
        
        elif self.value() == 'no_feedback':
            # Filter steps with no feedback
            no_feedback_ids = []
            for step in queryset:
                if step.get_feedback_summary()['total'] == 0:
                    no_feedback_ids.append(step.id)
            return queryset.filter(id__in=no_feedback_ids)
        
        return queryset

# UserProfile admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'school')

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'navbar_color_preview', 'button_color_preview', 'is_active', 'user_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'short_name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'user_count')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_name', 'description', 'is_active')
        }),
        ('Branding', {
            'fields': ('logo', 'navbar_color', 'primary_button_color'),
            'description': 'Logo and color scheme used for white-labeling the application'
        }),
        ('Contact Information', {
            'fields': ('website_url', 'address')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'user_count'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Number of Users'
    
    def navbar_color_preview(self, obj):
        if obj.navbar_color:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
                obj.navbar_color,
                obj.navbar_color
            )
        return "Default"
    navbar_color_preview.short_description = 'Navbar Color'
    
    def button_color_preview(self, obj):
        if obj.primary_button_color:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
                obj.primary_button_color,
                obj.primary_button_color
            )
        return "Default"
    button_color_preview.short_description = 'Button Color'

# UserProfile should only be managed through User admin, not directly
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'role', 'school', 'created_at')
#     list_filter = ('role', 'school', 'created_at')
#     search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'school__name')
#     readonly_fields = ('created_at', 'updated_at')
#     fieldsets = (
#         ('User Information', {
#             'fields': ('user', 'role', 'school')
#         }),
#         ('Metadata', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

class InstructionStepInline(admin.TabularInline):
    model = InstructionStep
    extra = 1
    fields = ('title', 'content', 'role', 'next_instruction', 'is_active')
    ordering = ('role', 'id')
    readonly_fields = ()
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly for non-admin users"""
        if obj and not request.user.is_superuser:
            return ()
        return ()

class GameStepInline(admin.TabularInline):
    model = GameStep
    extra = 1
    fields = ('step_number', 'title', 'estimated_duration_minutes', 'is_active')
    ordering = ('step_number',)
    readonly_fields = ()

@admin.register(GameStep)
class GameStepAdmin(admin.ModelAdmin):
    list_display = ('ai_game', 'step_number', 'title', 'instruction_count', 'estimated_duration_minutes', 'is_active')
    list_filter = ('ai_game', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'ai_game__title')
    inlines = [InstructionStepInline]
    ordering = ('ai_game', 'step_number')
    
    def instruction_count(self, obj):
        """Count of instruction steps for this game step"""
        return obj.instruction_steps.filter(is_active=True).count()
    instruction_count.short_description = 'Instructions'

@admin.register(AiGame)
class AiGameAdmin(admin.ModelAdmin):
    list_display = ('title', 'game_step_count', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)
    inlines = [GameStepInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
    )
    
    def game_step_count(self, obj):
        """Count of game steps for this game"""
        return obj.steps.filter(is_active=True).count()
    game_step_count.short_description = 'Game Steps'

class InstructionStepFeedbackInline(admin.TabularInline):
    model = InstructionStepFeedback
    extra = 0
    readonly_fields = ('user', 'is_helpful', 'feedback_comment', 'created_at')
    fields = ('user', 'is_helpful', 'feedback_comment', 'created_at')
    can_delete = False
    max_num = 0  # Prevent adding new feedback through admin
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(InstructionStep)
class InstructionStepAdmin(admin.ModelAdmin):
    list_display = ('game_step', 'title', 'role', 'is_active', 'feedback_summary', 'problematic_status', 'created_at')
    list_filter = ('game_step__ai_game', 'role', 'is_active', 'created_at', ProblematicStepFilter)
    search_fields = ('title', 'content', 'game_step__title', 'game_step__ai_game__title')
    ordering = ('game_step__ai_game', 'game_step__step_number', 'role', 'id')
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'feedback_summary_detailed', 'problematic_analysis')
    inlines = [InstructionStepFeedbackInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('game_step', 'title', 'role', 'is_active')
        }),
        ('Content', {
            'fields': ('content',),
            'description': 'The instruction content for this step and role.'
        }),
        ('Linking', {
            'fields': ('next_instruction',),
            'description': 'Link to next instruction in the sequence.'
        }),
        ('Feedback Analysis', {
            'fields': ('feedback_summary_detailed', 'problematic_analysis'),
            'classes': ('collapse',),
            'description': 'User feedback statistics and problematic step analysis.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['split_step', 'reorder_steps', 'reset_feedback', 'mark_as_reviewed']
    
    def problematic_status(self, obj):
        """Display problematic status with visual indicators"""
        if obj.is_problematic():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Problematic</span>')
        elif obj.has_recent_negative_feedback():
            return format_html('<span style="color: orange;">⚡ Recent Issues</span>')
        else:
            return format_html('<span style="color: green;">✅ Good</span>')
    problematic_status.short_description = 'Status'
    
    def role_display(self, obj):
        """Display role with color coding"""
        if obj.role == 'teacher':
            return format_html('<span style="color: blue; font-weight: bold;">👩‍🏫 Teacher</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">👨‍🎓 Student</span>')
    role_display.short_description = 'Role'
    
    def problematic_analysis(self, obj):
        """Display detailed problematic analysis"""
        reasons = obj.get_problematic_reasons()
        summary = obj.get_feedback_summary()
        
        if not reasons and summary['total'] == 0:
            return format_html('<p><em>No feedback received yet.</em></p>')
        
        if not reasons:
            return format_html(
                '<div style="background: #d4edda; padding: 10px; border-radius: 5px; color: #155724;">'
                '<h4>✅ Step Performance: Good</h4>'
                '<p>This step is performing well with no identified issues.</p>'
                '</div>'
            )
        
        html = '<div style="background: #f8d7da; padding: 10px; border-radius: 5px; color: #721c24;">'
        html += '<h4>⚠️ Issues Identified</h4><ul>'
        for reason in reasons:
            html += f'<li>{reason}</li>'
        html += '</ul>'
        
        # Add recent negative feedback details
        if obj.has_recent_negative_feedback():
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=7)
            recent_feedback = obj.feedback.filter(
                is_helpful=False,
                created_at__gte=cutoff_date
            ).order_by('-created_at')
            
            if recent_feedback.exists():
                html += '<h5>Recent Negative Feedback:</h5><ul>'
                for feedback in recent_feedback[:3]:  # Show latest 3
                    comment = feedback.feedback_comment[:50] + '...' if len(feedback.feedback_comment) > 50 else feedback.feedback_comment
                    html += f'<li><strong>{feedback.user.username}</strong> ({feedback.created_at.strftime("%m/%d %H:%M")})'
                    if comment:
                        html += f': "{comment}"'
                    html += '</li>'
                html += '</ul>'
        
        html += '<p style="margin-top: 10px;"><strong>Recommendation:</strong> Review and consider updating this step.</p>'
        html += '</div>'
        
        return format_html(html)
    problematic_analysis.short_description = 'Detailed Analysis'
    
    def feedback_summary(self, obj):
        """Display a short feedback summary in the list view"""
        summary = obj.get_feedback_summary()
        if summary['total'] == 0:
            return "No feedback"
        return f"👍 {summary['thumbs_up']} / 👎 {summary['thumbs_down']} ({summary['percentage_positive']}% positive)"
    feedback_summary.short_description = 'User Feedback'
    
    def feedback_summary_detailed(self, obj):
        """Display detailed feedback summary in the form view"""
        summary = obj.get_feedback_summary()
        if summary['total'] == 0:
            return format_html('<p><em>No user feedback yet.</em></p>')
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<h4>Feedback Summary</h4>'
            '<ul>'
            '<li><strong>Total feedback:</strong> {total}</li>'
            '<li><strong>👍 Thumbs up:</strong> {thumbs_up}</li>'
            '<li><strong>👎 Thumbs down:</strong> {thumbs_down}</li>'
            '<li><strong>Positive rate:</strong> {percentage_positive}%</li>'
            '</ul>'
            '</div>',
            total=summary['total'],
            thumbs_up=summary['thumbs_up'],
            thumbs_down=summary['thumbs_down'],
            percentage_positive=summary['percentage_positive']
        )
    feedback_summary_detailed.short_description = 'Detailed Feedback Summary'
    
    def split_step(self, request, queryset):
        """Admin action to split an instruction step into two steps"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one step to split.", level='error')
            return
        
        step = queryset.first()
        
        with transaction.atomic():
            # Create new step with next number
            new_step_number = step.step_number + 1
            step.reorder_steps_after_split(new_step_number)
            
            # Create the new step as a copy
            new_step = InstructionStep.objects.create(
                ai_game=step.ai_game,
                step_number=new_step_number,
                title=f"{step.title} (Part 2)",
                content="[Edit this content for the second part of the split step]",
                audience=step.audience,
                created_by=request.user
            )
            
            # Update original step title
            step.title = f"{step.title} (Part 1)"
            step.save()
            
        self.message_user(request, f"Step '{step.title}' has been split. Please edit both parts as needed.", level='success')
    split_step.short_description = "Split selected step into two steps"
    
    def reorder_steps(self, request, queryset):
        """Admin action to reorder steps (placeholder for future enhancement)"""
        self.message_user(request, "Step reordering functionality coming soon. For now, manually adjust step numbers.", level='info')
    reorder_steps.short_description = "Reorder steps (coming soon)"
    
    def reset_feedback(self, request, queryset):
        """Admin action to reset feedback for selected steps"""
        total_deleted = 0
        step_count = queryset.count()
        
        for step in queryset:
            deleted_count = step.reset_feedback()
            total_deleted += deleted_count
        
        self.message_user(
            request, 
            f"Reset feedback for {step_count} step(s). Removed {total_deleted} feedback record(s).", 
            level='success'
        )
    reset_feedback.short_description = "Reset feedback counters"
    
    def mark_as_reviewed(self, request, queryset):
        """Admin action to mark problematic steps as reviewed (add a note)"""
        # This could be extended to add a 'reviewed' flag or timestamp in the future
        reviewed_count = 0
        for step in queryset:
            if step.is_problematic() or step.has_recent_negative_feedback():
                reviewed_count += 1
        
        self.message_user(
            request,
            f"Marked {reviewed_count} problematic step(s) as reviewed. Consider updating content based on feedback.",
            level='info'
        )
    mark_as_reviewed.short_description = "Mark problematic steps as reviewed"
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new instruction steps"""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(InstructionStepFeedback)
class InstructionStepFeedbackAdmin(admin.ModelAdmin):
    list_display = ('instruction_step', 'user', 'feedback_display', 'created_at')
    list_filter = ('is_helpful', 'created_at', 'instruction_step__game_step__ai_game')
    search_fields = ('instruction_step__title', 'user__username', 'feedback_comment')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('instruction_step', 'user', 'is_helpful', 'feedback_comment')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def feedback_display(self, obj):
        """Display thumbs up/down in a user-friendly way"""
        return "👍 Helpful" if obj.is_helpful else "👎 Not helpful"
    feedback_display.short_description = 'Feedback'
    
    def has_add_permission(self, request):
        """Prevent manual addition of feedback through admin"""
        return False

class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1

class TeamGameParticipationInline(admin.TabularInline):
    model = TeamGameParticipation
    extra = 1

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_active', 'created_at', 'member_count', 'game_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    inlines = [TeamMembershipInline, TeamGameParticipationInline]
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'
    
    def game_count(self, obj):
        return obj.games.count()
    game_count.short_description = 'Games'

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'team__name')

@admin.register(TeamGameParticipation)
class TeamGameParticipationAdmin(admin.ModelAdmin):
    list_display = ('team', 'ai_game', 'is_active', 'joined_at')
    list_filter = ('is_active', 'joined_at')
    search_fields = ('team__name', 'ai_game__title')

@admin.register(GameResource)
class GameResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'team', 'ai_game', 'uploaded_by', 'resource_type', 'is_active', 'created_at')
    list_filter = ('resource_type', 'is_active', 'created_at')
    search_fields = ('title', 'team__name', 'ai_game__title', 'uploaded_by__username')
    readonly_fields = ('uploaded_by', 'created_at', 'updated_at')

@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ('invited_user', 'team', 'ai_game', 'invited_by', 'accepted', 'created_at')
    list_filter = ('accepted', 'created_at')
    search_fields = ('invited_user__username', 'team__name', 'invited_by__username')

# Note: Letter Density Game admin has been removed
# This functionality has been moved to the phoneme_density app

@admin.register(GameMatchup)
class GameMatchupAdmin(admin.ModelAdmin):
    list_display = ('ai_game', 'team1', 'team2', 'school', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'school', 'ai_game', 'created_at')
    search_fields = ('ai_game__title', 'team1__name', 'team2__name', 'school__name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'duration_minutes')
    fieldsets = (
        ('Matchup Details', {
            'fields': ('ai_game', 'team1', 'team2', 'school', 'created_by')
        }),
        ('Status and Timing', {
            'fields': ('status', 'scheduled_date', 'started_at', 'completed_at', 'duration_minutes')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_minutes(self, obj):
        return obj.duration_minutes
    duration_minutes.short_description = 'Duration (minutes)'
