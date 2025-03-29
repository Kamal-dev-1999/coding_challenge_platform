# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    # You can add additional fields here if needed.
    # For example:
    # phone_number = models.CharField(max_length=15, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


