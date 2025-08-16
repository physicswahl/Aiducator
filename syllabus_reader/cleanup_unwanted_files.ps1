#!/usr/bin/env powershell
# cleanup_unwanted_files.ps1
# Run this script to remove unwanted files that keep reappearing
# 
# NOTE: Files may reappear due to GitHub Copilot's "keep" function
# which can restore files from previous chat interactions.
# If files reappear, run this script again or avoid using "keep" 
# on unwanted file suggestions.

$projectRoot = "c:\Users\david\Desktop\Aiducator\syllabus_reader"
cd $projectRoot

# List of unwanted files/patterns
$unwantedFiles = @(
    "associate_phoneme_game.py",
    "cleanup_letter_density.py", 
    "cleanup_letter_density_matchups.py",
    "create_sample_instructions.py",
    "create_test_feedback.py", 
    "remove_letter_density_game.py",
    "remove_letter_density_game_final.py",
    "update_instruction_content.py",
    "update_url_patterns.py",
    "PROBLEMATIC_STEPS_DOCS.md",
    "TEACHER_STUDENT_INSTRUCTIONS.md",
    "INSTRUCTION_SYSTEM_DOCS.md",
    "LINKED_INSTRUCTION_SYSTEM.md",
    "fix_url_patterns.py",
    "check_url_patterns.py", 
    "update_url_patterns.py",
    "aigames\management\commands\set_lgb_navbar_color.py",
    "aigames\management\commands\set_lgb_button_color.py",
    ".gitignore",
    
    # Phoneme density app cleanup - orphaned templates and views
    "phoneme_density\templates\phoneme_density\dashboard.html",
    "phoneme_density\templates\phoneme_density\create_game.html", 
    "phoneme_density\templates\phoneme_density\game_detail.html",
    "phoneme_density\templates\phoneme_density\phoneme_step_base.html",
    "phoneme_density\templates\phoneme_density\step1_analysis.html",
    "phoneme_density\templates\phoneme_density\matchup_step1_analysis.html",
    "phoneme_density\templates\phoneme_density\matchup_step2_comparison.html",
    "phoneme_density\templates\phoneme_density\matchup_step3_rules.html",
    "phoneme_density\views_new.py",
    "phoneme_density\models_new.py",
    "phoneme_density\forms_new.py",
    
    # Management commands cleanup - one-time setup commands
    "aigames\management\commands\setup_lgb_school.py",
    "aigames\management\commands\set_lgb_button_color.py",
    "aigames\management\commands\setup_user_roles.py", 
    "aigames\management\commands\check_game_steps.py",
    
    # Obsolete game management templates (bypassed matchup system)
    "aigames\templates\aigames\create_aigame.html",
    "aigames\templates\aigames\list_aigames.html",
    "aigames\templates\aigames\game_form.html", 
    "aigames\templates\aigames\manage_games.html",
    "aigames\templates\aigames\manage_game_detail.html",
    "aigames\templates\aigames\game_step_form.html",
    "aigames\templates\aigames\game_instructions.html",
    "aigames\templates\aigames\teacher_game_instructions.html"
)

$unwantedDirs = @(
    "aigames\templates\aigames\letter_density",
    
    # Cache directories that can be safely removed
    "phoneme_density\__pycache__",
    "aigames\management\commands\__pycache__",
    "aigames\management\__pycache__"
)

Write-Host "🧹 Cleaning up unwanted files..." -ForegroundColor Yellow

# Remove unwanted files
foreach ($file in $unwantedFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "✅ Removed: $file" -ForegroundColor Green
    }
}

# Remove unwanted directories
foreach ($dir in $unwantedDirs) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force
        Write-Host "✅ Removed directory: $dir" -ForegroundColor Green
    }
}

Write-Host "🎉 Cleanup complete!" -ForegroundColor Green
