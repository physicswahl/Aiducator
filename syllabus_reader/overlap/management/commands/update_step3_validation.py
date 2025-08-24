from django.core.management.base import BaseCommand
from aigames.models import AiGame, GameStep


class Command(BaseCommand):
    help = 'Update overlap game step 3 to require validation'
    
    def handle(self, *args, **options):
        try:
            # Find the overlap game
            overlap_game = AiGame.objects.filter(title__icontains='overlap').first()
            
            if not overlap_game:
                self.stdout.write(
                    self.style.ERROR('Overlap game not found. Please ensure the overlap game exists.')
                )
                return
            
            # Find step 3 of the overlap game
            step3 = GameStep.objects.filter(ai_game=overlap_game, step_number=3).first()
            
            if not step3:
                self.stdout.write(
                    self.style.ERROR(f'Step 3 not found for game: {overlap_game.title}')
                )
                return
            
            # Update step 3 to require validation
            step3.requires_validation = True
            step3.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated step 3 "{step3.title}" of game "{overlap_game.title}" to require validation.'
                )
            )
            
            # Display current status
            self.stdout.write(f'\nCurrent status:')
            self.stdout.write(f'Game: {overlap_game.title}')
            self.stdout.write(f'Step: {step3.step_number} - {step3.title}')
            self.stdout.write(f'Requires Validation: {step3.requires_validation}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating step 3: {str(e)}')
            )
