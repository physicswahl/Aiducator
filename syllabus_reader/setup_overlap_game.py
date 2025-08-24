#!/usr/bin/env python
"""
Script to create the Overlap Game in the AIgames system.
This creates an AiGame record and GameStep records for the 4-step overlap game.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/david/Desktop/Aiducator/syllabus_reader')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syllabus_reader.settings')
django.setup()

from aigames.models import AiGame, GameStep

def create_overlap_game():
    """Create the overlap game and its steps"""
    
    # Create or get the overlap game
    overlap_game, created = AiGame.objects.get_or_create(
        title="Overlap Detection Game",
        defaults={
            'description': "A 4-step game where teams configure overlap detection parameters, collect data, analyze patterns, and draw conclusions from overlap analysis."
        }
    )
    
    if created:
        print(f"✅ Created new AiGame: {overlap_game.title}")
    else:
        print(f"📋 Found existing AiGame: {overlap_game.title}")
    
    # Define the 4 steps for the overlap game
    steps_data = [
        {
            'step_number': 1,
            'title': 'Setup & Configuration',
            'description': 'Configure overlap detection parameters and initialize the system',
            'url_pattern': 'overlap:step1',
            'estimated_duration_minutes': 10
        },
        {
            'step_number': 2,
            'title': 'Data Collection',
            'description': 'Collect data points and establish baseline measurements',
            'url_pattern': 'overlap:step2',
            'estimated_duration_minutes': 15
        },
        {
            'step_number': 3,
            'title': 'Analysis & Comparison',
            'description': 'Analyze overlap patterns and compare different scenarios',
            'url_pattern': 'overlap:step3',
            'estimated_duration_minutes': 20
        },
        {
            'step_number': 4,
            'title': 'Results & Conclusion',
            'description': 'Review results and draw conclusions from the overlap analysis',
            'url_pattern': 'overlap:step4',
            'estimated_duration_minutes': 15
        }
    ]
    
    # Create the game steps
    for step_data in steps_data:
        step, step_created = GameStep.objects.get_or_create(
            ai_game=overlap_game,
            step_number=step_data['step_number'],
            defaults={
                'title': step_data['title'],
                'description': step_data['description'],
                'url_pattern': step_data['url_pattern'],
                'estimated_duration_minutes': step_data['estimated_duration_minutes'],
                'is_active': True
            }
        )
        
        if step_created:
            print(f"✅ Created GameStep {step.step_number}: {step.title}")
        else:
            print(f"📋 Found existing GameStep {step.step_number}: {step.title}")
    
    print(f"\n🎮 Overlap Game Setup Complete!")
    print(f"Game ID: {overlap_game.id}")
    print(f"Total Steps: {overlap_game.steps.count()}")
    print(f"Total Duration: {overlap_game.get_total_estimated_duration()} minutes")
    print(f"Has Multiple Steps: {overlap_game.has_multiple_steps}")
    
    return overlap_game

if __name__ == "__main__":
    try:
        game = create_overlap_game()
        print(f"\n✨ Success! The Overlap Game is now available in the AIgames system.")
        print(f"Teachers can now create matchups and associate this game with units.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
