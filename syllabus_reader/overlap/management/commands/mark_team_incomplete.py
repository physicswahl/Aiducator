from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from aigames.models import Team, GameMatchup
from overlap.models import TeamOverlapData


class Command(BaseCommand):
    help = 'Mark a specific team as incomplete for a matchup'

    def add_arguments(self, parser):
        parser.add_argument('team_name', type=str, help='Name of the team to mark as incomplete')
        parser.add_argument('--matchup-id', type=int, help='Specific matchup ID (optional)')
        parser.add_argument('--reset-to-step', type=int, default=1, help='Reset to specific step (default: 1)')

    def handle(self, *args, **options):
        team_name = options['team_name']
        matchup_id = options.get('matchup_id')
        reset_to_step = options['reset_to_step']

        try:
            # Find the team
            team = Team.objects.get(name=team_name)
            self.stdout.write(f"Found team: {team.name}")

            # Find matchups for this team
            if matchup_id:
                matchups = GameMatchup.objects.filter(
                    id=matchup_id
                ).filter(
                    models.Q(team1=team) | models.Q(team2=team)
                )
            else:
                matchups = GameMatchup.objects.filter(
                    models.Q(team1=team) | models.Q(team2=team)
                )

            if not matchups.exists():
                self.stdout.write(
                    self.style.ERROR(f"No matchups found for team {team_name}")
                )
                return

            with transaction.atomic():
                for matchup in matchups:
                    # Get or create team overlap data
                    team_data, created = TeamOverlapData.objects.get_or_create(
                        team=team,
                        matchup=matchup
                    )

                    # Reset progress
                    team_data.current_step = reset_to_step
                    team_data.step1_completed = False
                    team_data.step2_completed = False
                    team_data.step3_completed = False
                    team_data.step4_completed = False
                    team_data.game_completed = False
                    
                    # Clear data if resetting to step 1
                    if reset_to_step == 1:
                        team_data.circle_placement_submitted = False
                        team_data.analysis_complete = False
                        team_data.baseline_established = False
                        team_data.final_score = None
                        team_data.evaluation_clicks = []
                        team_data.click_count = 0
                    
                    team_data.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Marked team {team_name} as incomplete for matchup {matchup.id} "
                            f"(reset to step {reset_to_step})"
                        )
                    )

        except Team.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Team '{team_name}' not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            )
