from django.contrib import admin
from .models import TeamStep4Data, TeamText, PhonemeGuess, TextGuess


@admin.register(TeamStep4Data)
class TeamStep4DataAdmin(admin.ModelAdmin):
    list_display = ['team', 'matchup', 'selected_phoneme', 'created_at']
    list_filter = ['matchup', 'selected_phoneme', 'created_at']
    search_fields = ['team__name', 'matchup__ai_game__title']


@admin.register(TeamText)
class TeamTextAdmin(admin.ModelAdmin):
    list_display = ['step4_data', 'text_number', 'approval_status', 'phoneme_density', 'reviewed_by']
    list_filter = ['approval_status', 'step4_data__matchup', 'reviewed_by']
    search_fields = ['step4_data__team__name', 'content']


@admin.register(PhonemeGuess)
class PhonemeGuessAdmin(admin.ModelAdmin):
    list_display = ['guessing_team', 'target_team', 'matchup', 'phoneme_guess', 'created_at']
    list_filter = ['matchup', 'phoneme_guess', 'created_at']
    search_fields = ['guessing_team__name', 'target_team__name', 'rule_description']


@admin.register(TextGuess)
class TextGuessAdmin(admin.ModelAdmin):
    list_display = ['phoneme_guess', 'text_number', 'follows_rule', 'created_at']
    list_filter = ['follows_rule', 'phoneme_guess__matchup', 'text_number']
    search_fields = ['phoneme_guess__guessing_team__name']
