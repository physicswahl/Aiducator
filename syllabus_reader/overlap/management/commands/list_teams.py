from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from aigames.models import Team, GameMatchup
from overlap.models import TeamOverlapData


class Command(BaseCommand):
    help = 'List all teams and their current overlap game status'

    def handle(self, *args, **options):
        try:
            # List all teams
            teams = Team.objects.all()
            
            if not teams.exists():
                self.stdout.write(self.style.ERROR("No teams found in the database"))
                return
                
            self.stdout.write("Available teams:")
            self.stdout.write("-" * 50)
            
            for team in teams:
                self.stdout.write(f"Team ID: {team.id}, Name: '{team.name}'")
                
                # Check if team has overlap data
                team_data = TeamOverlapData.objects.filter(team=team)
                if team_data.exists():
                    for data in team_data:
                        self.stdout.write(f"  - Matchup {data.matchup.id}: Step {data.current_step}, Game Complete: {data.game_completed}")
                else:
                    self.stdout.write("  - No overlap game data")
                
                self.stdout.write("")  # Empty line for readability

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
