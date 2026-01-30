from django.db import models
from django.contrib.auth.models import User


class RM(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    # for round-robin assignment
    last_assigned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
