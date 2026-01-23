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
        choices=[('open', 'Open'), ('closed', 'Closed')],
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE
    )
    direction = models.CharField(
        max_length=3,
        choices=[('in', 'Incoming'), ('out', 'Outgoing')]
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
