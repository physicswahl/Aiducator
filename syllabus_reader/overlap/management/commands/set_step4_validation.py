from django.core.management.base import BaseCommand
from aigames.models import AiGame, GameStep


class Command(BaseCommand):
    help = 'Set step 4 of the overlap game to require validation'

    def handle(self, *args, **options):
        try:
            # Find the overlap game
            overlap_game = AiGame.objects.filter(title__icontains='overlap').first()
            
            if not overlap_game:
                self.stdout.write(
                    self.style.ERROR('No overlap game found. Please create the overlap game first.')
                )
                return
            
            # Find step 4 of the overlap game
            step4 = GameStep.objects.filter(ai_game=overlap_game, step_number=4).first()
            
            if not step4:
                self.stdout.write(
                    self.style.ERROR('Step 4 not found for the overlap game.')
                )
                return
            
            # Check current status
            if step4.requires_validation:
                self.stdout.write(
                    self.style.WARNING(f'Step 4 "{step4.title}" already requires validation.')
                )
                return
            
            # Set requires_validation to True
            step4.requires_validation = True
            step4.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully set step 4 "{step4.title}" to require validation.'
                )
            )
            
            # Show current status of all steps
            self.stdout.write('\nCurrent validation status for all overlap game steps:')
            for step in overlap_game.steps.all().order_by('step_number'):
                status = "✓ Requires validation" if step.requires_validation else "✗ No validation required"
                self.stdout.write(f'  Step {step.step_number}: {step.title} - {status}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred: {str(e)}')
            )
