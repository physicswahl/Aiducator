from django.core.management.base import BaseCommand
from overlap.models import TeamOverlapData
from aigames.models import GameMatchup

class Command(BaseCommand):
    help = 'Debug step 4 data issues'

    def add_arguments(self, parser):
        parser.add_argument('matchup_id', type=int, help='Matchup ID to debug')

    def handle(self, *args, **options):
        matchup_id = options['matchup_id']
        
        try:
            matchup = GameMatchup.objects.get(id=matchup_id)
            self.stdout.write(f"Matchup: {matchup}")
            self.stdout.write(f"Team 1: {matchup.team1}")
            self.stdout.write(f"Team 2: {matchup.team2}")
            
            # Check both teams' data
            for team in [matchup.team1, matchup.team2]:
                try:
                    team_data = TeamOverlapData.objects.get(team=team, matchup=matchup)
                    self.stdout.write(f"\n--- {team.name} Data ---")
                    self.stdout.write(f"Circle position: ({team_data.circle_x}, {team_data.circle_y})")
                    self.stdout.write(f"Step 3 completed: {team_data.step3_completed}")
                    self.stdout.write(f"Step 4 points: {len(team_data.step4_points or [])}")
                    self.stdout.write(f"Step 4 score: {team_data.step4_total_score}")
                    
                    if team_data.step4_points:
                        for i, point in enumerate(team_data.step4_points):
                            self.stdout.write(f"  Point {i+1}: {point}")
                            
                except TeamOverlapData.DoesNotExist:
                    self.stdout.write(f"No data found for team {team.name}")
                    
        except GameMatchup.DoesNotExist:
            self.stdout.write(f"Matchup {matchup_id} not found")
