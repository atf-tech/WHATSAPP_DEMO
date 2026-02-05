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
    unread_count = models.PositiveIntegerField(default=0)


    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_preview = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor.phone_number} → {self.rm.name}"

class Message(models.Model):
    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
    ]
    
    MESSAGE_TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("document", "Document"),
    ]

    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default="text"
    )


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
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]



class MessageMedia(models.Model):
    message = models.OneToOneField(
        Message,
        related_name="media",
        on_delete=models.CASCADE
    )

    file = models.FileField(upload_to="whatsapp_media/")
    mime_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()

    # WhatsApp Cloud media id
    wa_media_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)



class MessageReaction(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reactions"
    )
    rm = models.ForeignKey(
        "accounts.RM",
        on_delete=models.CASCADE
    )
    emoji = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("message", "rm")
        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["rm"]),
        ]

    def __str__(self):
        return f"{self.rm} reacted {self.emoji} on msg {self.message_id}"

