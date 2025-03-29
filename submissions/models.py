# submissions/models.py
from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem
from django.conf import settings
class Submission(models.Model):
    RESULT_CHOICES = (
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Runtime Error', 'Runtime Error'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    result = models.CharField(max_length=50, choices=RESULT_CHOICES, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.user.username} for {self.problem.title}"
