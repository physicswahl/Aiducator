from django.db import models

class Provider(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Curriculum(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(help_text="When this curriculum becomes effective")
    end_date = models.DateField(null=True, blank=True, help_text="When this curriculum expires (leave blank if still current)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider.name} - {self.title}"
    
    @property
    def is_current(self):
        """Check if the curriculum is currently active based on date range"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.end_date:
            return self.start_date <= today <= self.end_date
        return self.start_date <= today

class Syllabus(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.curriculum.title} - {self.name}"

class Unit(models.Model):
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ai_game = models.ForeignKey('aigames.AiGame', on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional AI game associated with this unit")

    def __str__(self):
        return f"{self.title} ({self.syllabus})"