from django.core.management.base import BaseCommand
from aigames.models import AiGame, GameStep

class Command(BaseCommand):
    help = 'Update URL patterns for detector game steps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--game-id',
            type=int,
            help='Specific game ID to update (optional - if not provided, will update all games with "detector" in the title)',
        )

    def handle(self, *args, **options):
        game_id = options.get('game_id')
        
        if game_id:
            try:
                games = [AiGame.objects.get(id=game_id)]
                self.stdout.write(f"Updating game ID {game_id}")
            except AiGame.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Game with ID {game_id} not found"))
                return
        else:
            # Find games that likely need detector URLs (contain "detector" in title)
            games = AiGame.objects.filter(title__icontains='detector')
            if not games:
                self.stdout.write(self.style.WARNING("No games found with 'detector' in the title"))
                self.stdout.write("Available games:")
                for game in AiGame.objects.all():
                    self.stdout.write(f"  ID {game.id}: {game.title}")
                return
            
            self.stdout.write(f"Found {games.count()} detector games to update")

        for game in games:
            self.stdout.write(f"\nUpdating game: {game.title} (ID: {game.id})")
            
            # Update or create the 4 detector steps
            detector_steps = [
                (1, 'Data Collection Setup', 'detector:step1'),
                (2, 'CO2 Monitoring', 'detector:step2'), 
                (3, 'Data Analysis', 'detector:step3'),
                (4, 'Report Generation', 'detector:step4'),
            ]
            
            for step_number, title, url_pattern in detector_steps:
                step, created = GameStep.objects.get_or_create(
                    ai_game=game,
                    step_number=step_number,
                    defaults={
                        'title': title,
                        'url_pattern': url_pattern,
                        'description': f'Detector game step {step_number}',
                        'is_active': True
                    }
                )
                
                if not created:
                    # Update existing step
                    step.title = title
                    step.url_pattern = url_pattern
                    step.description = f'Detector game step {step_number}'
                    step.is_active = True
                    step.save()
                    self.stdout.write(f"  Updated Step {step_number}: {title} -> {url_pattern}")
                else:
                    self.stdout.write(f"  Created Step {step_number}: {title} -> {url_pattern}")
            
            # Mark game as having multiple steps
            if not game.has_multiple_steps:
                game.has_multiple_steps = True
                game.save()
                self.stdout.write(f"  Marked game as having multiple steps")

        self.stdout.write(self.style.SUCCESS("\nURL patterns updated successfully!"))
        self.stdout.write("You can now test the detector game from the student dashboard.")
