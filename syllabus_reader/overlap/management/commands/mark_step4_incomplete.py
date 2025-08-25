from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from aigames.models import Team, GameMatchup, MatchupStepProgress, GameStep
from overlap.models import TeamOverlapData


class Command(BaseCommand):
    help = 'Mark a team as incomplete for overlap game step 4'

    def add_arguments(self, parser):
        parser.add_argument('team_name', type=str, help='Name of the team to mark as incomplete')

    def handle(self, *args, **options):
        team_name = options['team_name']
        
        try:
            with transaction.atomic():
                # Find the team
                try:
                    team = Team.objects.get(name=team_name)
                    self.stdout.write(f"Found team: {team.name}")
                except Team.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Team '{team_name}' not found"))
                    self.stdout.write("Available teams:")
                    for t in Team.objects.all():
                        self.stdout.write(f"  - {t.name}")
                    return

                # Find all matchups for this team
                matchups = GameMatchup.objects.filter(
                    models.Q(team1=team) | models.Q(team2=team)
                )

                if not matchups.exists():
                    self.stdout.write(self.style.ERROR(f"No matchups found for team {team_name}"))
                    return

                for matchup in matchups:
                    # Get or create team overlap data
                    team_data, created = TeamOverlapData.objects.get_or_create(
                        team=team,
                        matchup=matchup
                    )

                    # Mark step 4 as incomplete
                    team_data.step4_completed = False
                    team_data.game_completed = False
                    
                    # Clear step 4 specific data
                    team_data.final_score = None
                    team_data.evaluation_clicks = []
                    team_data.click_count = 0
                    team_data.evaluation_strategy = ""
                    
                    # Reset to step 3 if currently on step 4
                    if team_data.current_step >= 4:
                        team_data.current_step = 3
                    
                    team_data.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Marked team {team_name} step 4 as incomplete for matchup {matchup.id}"
                        )
                    )

                    # Also mark MatchupStepProgress for step 4 as incomplete
                    try:
                        step4 = GameStep.objects.get(ai_game=matchup.ai_game, step_number=4)
                        step_progress, created = MatchupStepProgress.objects.get_or_create(
                            matchup=matchup,
                            game_step=step4
                        )
                        step_progress.is_completed = False
                        step_progress.completed_at = None
                        step_progress.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Marked MatchupStepProgress for step 4 as incomplete for matchup {matchup.id}"
                            )
                        )
                    except GameStep.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Step 4 not found for game {matchup.ai_game.title}"
                            )
                        )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
