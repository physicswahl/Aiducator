from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from aigames.models import Team, GameMatchup
from overlap.models import TeamOverlapData


class Command(BaseCommand):
    help = 'Mark team 5A as incomplete for overlap game'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Find team 5A
                try:
                    team = Team.objects.get(name='5A')
                    self.stdout.write(f"Found team: {team.name}")
                except Team.DoesNotExist:
                    self.stdout.write(self.style.ERROR("Team '5A' not found"))
                    return

                # Find all matchups for team 5a
                matchups = GameMatchup.objects.filter(
                    models.Q(team1=team) | models.Q(team2=team)
                )

                if not matchups.exists():
                    self.stdout.write(self.style.ERROR("No matchups found for team 5A"))
                    return

                for matchup in matchups:
                    # Get or create team overlap data
                    team_data, created = TeamOverlapData.objects.get_or_create(
                        team=team,
                        matchup=matchup
                    )

                    # Mark as incomplete - reset to step 1
                    team_data.current_step = 1
                    team_data.step1_completed = False
                    team_data.step2_completed = False
                    team_data.step3_completed = False
                    team_data.step4_completed = False
                    team_data.game_completed = False
                    
                    # Clear game data
                    team_data.circle_placement_submitted = False
                    team_data.analysis_complete = False
                    team_data.baseline_established = False
                    team_data.final_score = None
                    team_data.evaluation_clicks = []
                    team_data.click_count = 0
                    team_data.evaluation_strategy = ""
                    
                    team_data.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully marked team 5a as incomplete for matchup {matchup.id}"
                        )
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
