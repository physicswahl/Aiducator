from django.core.management.base import BaseCommand
from aigames.models import GameMatchup, TeamStepValidation


class Command(BaseCommand):
    help = 'Reset team validation status for a specific matchup and step'

    def add_arguments(self, parser):
        parser.add_argument('matchup_id', type=int, help='Matchup ID')
        parser.add_argument('step_number', type=int, help='Step number')

    def handle(self, *args, **options):
        matchup_id = options['matchup_id']
        step_number = options['step_number']
        
        try:
            matchup = GameMatchup.objects.get(id=matchup_id)
            self.stdout.write(f"Found matchup: {matchup}")
            
            # Get the game step
            game_step = matchup.ai_game.get_step_by_number(step_number)
            if not game_step:
                self.stdout.write(self.style.ERROR(f"Step {step_number} not found"))
                return
            
            self.stdout.write(f"Found step: {game_step}")
            
            # Reset validation for both teams
            validations = TeamStepValidation.objects.filter(
                matchup=matchup,
                game_step=game_step
            )
            
            self.stdout.write(f"Found {validations.count()} validation records")
            
            for validation in validations:
                validation.is_validated = False
                validation.validated_at = None
                validation.validated_by = None
                validation.save()
                self.stdout.write(f"Reset validation for {validation.team.name}")
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully reset validation status for matchup {matchup_id}, step {step_number}"
            ))
            
        except GameMatchup.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Matchup {matchup_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
