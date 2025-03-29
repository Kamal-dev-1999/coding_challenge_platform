# problems/models.py
from django.db import models

class Problem(models.Model):
    DIFFICULTY_CHOICES = (
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    constraints = models.TextField(blank=True, null=True)
    sample_input = models.TextField(blank=True, null=True)
    sample_output = models.TextField(blank=True, null=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='Easy')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
