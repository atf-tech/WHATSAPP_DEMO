from django.db import models
from accounts.models import RM


class Donor(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_number


class Conversation(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    rm = models.ForeignKey(RM, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=10,
        choices=[("open", "Open"), ("closed", "Closed")],
        default="open"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 critical for inbox + realtime
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_preview = models.TextField(blank=True)

    # 🔒 future locking support
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor.phone_number} → {self.rm.name}"

class Message(models.Model):
    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE
    )

    direction = models.CharField(
        max_length=3,
        choices=[("in", "Incoming"), ("out", "Outgoing")]
    )

    body = models.TextField(blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="sent"
    )

    external_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
