import json
import hmac
import hashlib
from django.utils import timezone

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from accounts.models import RM
from chat.models import Donor, Conversation, Message


VERIFY_TOKEN = settings.VERIFY_TOKEN


def verify_signature(request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return False

    expected = "sha256=" + hmac.new(
        settings.WA_APP_SECRET.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@csrf_exempt
def webhook(request):

    # Webhook verification
    if request.method == "GET":
        if request.GET.get("hub.verify_token") == VERIFY_TOKEN:
            return HttpResponse(request.GET.get("hub.challenge"))
        return HttpResponse("Invalid token", status=403)

    # Message receive
    if request.method == "POST":

        if not verify_signature(request):
            return HttpResponse(status=403)

        payload = json.loads(request.body)

        try:
            value = payload["entry"][0]["changes"][0]["value"]
            msg = value["messages"][0]

            msg_id = msg["id"]
            donor_number = msg["from"]
            text = msg.get("text", {}).get("body")

            if not text:
                return JsonResponse({"status": "ignored"})
        except Exception:
            return JsonResponse({"status": "ignored"})

        # Prevent duplicates
        if Message.objects.filter(external_id=msg_id).exists():
            return JsonResponse({"status": "duplicate"})

        with transaction.atomic():

            donor, _ = Donor.objects.get_or_create(
                phone_number=donor_number
            )

            conversation = Conversation.objects.select_for_update().filter(
                donor=donor,
                status="open"
            ).first()

            if not conversation:
                rm = RM.objects.filter(is_active=True).order_by("last_assigned").first()
                conversation = Conversation.objects.create(
                    donor=donor,
                    rm=rm
                )
                rm.last_assigned = conversation.created_at
                rm.save(update_fields=["last_assigned"])

            message = Message.objects.create(
                conversation=conversation,
                direction="in",
                body=text,
                external_id=msg_id,
                status="delivered"
            )

        local_time = timezone.localtime(message.created_at)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation.id}",
            {
                "type": "chat_message",
                "message": {
                    "body": message.body,
                    "direction": "in",
                    "time": local_time.strftime("%I:%M %p"),
                }
            }
        )
        
        return JsonResponse({"status": "ok"})
