from django.core.management.base import BaseCommand
from aigames.models import AiGame, GameStep


class Command(BaseCommand):
    help = 'Create a sample Detector AI Game with steps'

    def handle(self, *args, **options):
        # Create the Detector AI Game
        detector_game, created = AiGame.objects.get_or_create(
            title="Detector Game",
            defaults={
                'description': "A 4-step interactive detection and analysis game where teams work together to identify patterns, collect data, analyze results, and present findings."
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created AI Game: {detector_game.title}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'AI Game already exists: {detector_game.title}')
            )
        
        # Create the 4 game steps
        steps_data = [
            {
                'step_number': 1,
                'title': 'Setup & Preparation',
                'description': 'Team setup, role assignment, and initial preparation phase.',
                'estimated_duration_minutes': 15
            },
            {
                'step_number': 2,
                'title': 'Data Collection',
                'description': 'Systematic data collection and initial observations.',
                'estimated_duration_minutes': 25
            },
            {
                'step_number': 3,
                'title': 'Analysis & Processing',
                'description': 'Data analysis, pattern recognition, and hypothesis formation.',
                'estimated_duration_minutes': 30
            },
            {
                'step_number': 4,
                'title': 'Results & Presentation',
                'description': 'Final results compilation and team presentation.',
                'estimated_duration_minutes': 20
            }
        ]
        
        for step_data in steps_data:
            step, step_created = GameStep.objects.get_or_create(
                ai_game=detector_game,
                step_number=step_data['step_number'],
                defaults={
                    'title': step_data['title'],
                    'description': step_data['description'],
                    'estimated_duration_minutes': step_data['estimated_duration_minutes'],
                    'is_active': True
                }
            )
            
            if step_created:
                self.stdout.write(
                    self.style.SUCCESS(f'  Created Step {step.step_number}: {step.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  Step {step.step_number} already exists: {step.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Detector game setup complete! You can now associate this game with units.')
        )
