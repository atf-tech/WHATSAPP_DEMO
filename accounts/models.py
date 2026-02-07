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



class PushSubscription(models.Model):
    rm = models.ForeignKey(
        RM,
        on_delete=models.CASCADE,
        related_name="push_subscriptions"
    )

    # ✅ FIX: Text → CharField
    endpoint = models.CharField(max_length=512, unique=True)

    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)

    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PushSub for {self.rm.name}"
