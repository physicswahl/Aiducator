from django.core.management.base import BaseCommand
from aigames.models import GameMatchup, MatchupStepProgress


class Command(BaseCommand):
    help = 'Mark a specific step as incomplete for a matchup'

    def add_arguments(self, parser):
        parser.add_argument('matchup_id', type=int, help='ID of the matchup')
        parser.add_argument('step_number', type=int, help='Step number to mark incomplete')

    def handle(self, *args, **options):
        matchup_id = options['matchup_id']
        step_number = options['step_number']
        
        try:
            matchup = GameMatchup.objects.get(id=matchup_id)
            self.stdout.write(f"Found matchup: {matchup}")
            
            # Get the game step
            game_step = matchup.ai_game.get_step_by_number(step_number)
            if not game_step:
                self.stdout.write(
                    self.style.ERROR(f'Step {step_number} not found for this game')
                )
                return
            
            # Find the progress record
            try:
                progress = MatchupStepProgress.objects.get(
                    matchup=matchup,
                    game_step=game_step
                )
                
                # Mark as incomplete
                progress.is_completed = False
                progress.completed_at = None
                progress.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully marked Step {step_number} as incomplete for matchup {matchup_id}'
                    )
                )
                
            except MatchupStepProgress.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'No progress record found for Step {step_number} in matchup {matchup_id}')
                )
                
        except GameMatchup.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Matchup with ID {matchup_id} not found')
            )
