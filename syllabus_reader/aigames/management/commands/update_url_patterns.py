from django.core.management.base import BaseCommand
from aigames.models import GameStep

class Command(BaseCommand):
    help = 'Update GameStep url_pattern values to use simplified step names'

    def handle(self, *args, **options):
        # Update the URL patterns for phoneme density game steps
        updates = [
            (1, 'phoneme_density:step1'),
            (2, 'phoneme_density:step2'),
            (3, 'phoneme_density:step3'),
            (4, 'phoneme_density:step4'),
            (5, 'phoneme_density:step5'),
            (6, 'phoneme_density:step6'),
        ]
        
        for step_number, new_pattern in updates:
            try:
                # Find GameSteps for phoneme density game
                game_steps = GameStep.objects.filter(
                    step_number=step_number,
                    ai_game__title__icontains='phoneme'
                )
                
                for game_step in game_steps:
                    old_pattern = game_step.url_pattern
                    game_step.url_pattern = new_pattern
                    game_step.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated step {step_number}: {old_pattern} -> {new_pattern}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating step {step_number}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS('URL pattern update complete!'))
