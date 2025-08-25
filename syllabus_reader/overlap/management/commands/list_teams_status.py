from django.core.management.base import BaseCommand
from django.db import models
from aigames.models import Team, GameMatchup, MatchupStepProgress
from overlap.models import TeamOverlapData


class Command(BaseCommand):
    help = 'List all teams and their overlap game status'

    def handle(self, *args, **options):
        self.stdout.write("Available teams:")
        teams = Team.objects.all()
        
        for team in teams:
            self.stdout.write(f"  - {team.name} (ID: {team.id})")
            
            # Show matchups for this team
            matchups = GameMatchup.objects.filter(
                models.Q(team1=team) | models.Q(team2=team)
            )
            
            for matchup in matchups:
                self.stdout.write(f"    Matchup {matchup.id}: {matchup}")
                
                # Show overlap data
                try:
                    team_data = TeamOverlapData.objects.get(team=team, matchup=matchup)
                    self.stdout.write(f"      Current step: {team_data.current_step}")
                    self.stdout.write(f"      Step 4 completed: {team_data.step4_completed}")
                except TeamOverlapData.DoesNotExist:
                    self.stdout.write(f"      No overlap data found")
                
                # Show step progress
                step4_progress = MatchupStepProgress.objects.filter(
                    matchup=matchup,
                    game_step__step_number=4
                ).first()
                
                if step4_progress:
                    self.stdout.write(f"      Step 4 matchup progress: {step4_progress.is_completed}")
                else:
                    self.stdout.write(f"      No step 4 progress found")
                    
        self.stdout.write(f"\nTotal teams: {teams.count()}")
