import json
import hmac
import hashlib
import requests

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from accounts.models import RM
from chat.models import Donor, Conversation, Message, MessageMedia


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

    # -------------------------------------------------
    # Verification
    # -------------------------------------------------
    if request.method == "GET":
        if request.GET.get("hub.verify_token") == VERIFY_TOKEN:
            return HttpResponse(request.GET.get("hub.challenge"))
        return HttpResponse(status=403)

    if request.method != "POST":
        return HttpResponse(status=200)

    if not verify_signature(request):
        return HttpResponse(status=403)

    try:
        payload = json.loads(request.body)
        value = payload["entry"][0]["changes"][0]["value"]
    except Exception:
        return JsonResponse({"status": "ignored"})

    channel_layer = get_channel_layer()

    # -------------------------------------------------
    # STATUS UPDATES (ticks)
    # -------------------------------------------------
    for status_obj in value.get("statuses", []):
        wa_id = status_obj.get("id")
        wa_status = status_obj.get("status")

        if not wa_id or not wa_status:
            continue

        try:
            msg = Message.objects.get(external_id=wa_id)
        except Message.DoesNotExist:
            continue

        if wa_status == "delivered":
            msg.status = "delivered"
        elif wa_status == "read":
            msg.status = "read"
        else:
            continue

        msg.save(update_fields=["status"])

        async_to_sync(channel_layer.group_send)(
            f"chat_{msg.conversation.id}",
            {
                "type": "message_status",
                "message_id": msg.id,
                "status": msg.status,
            }
        )

    # -------------------------------------------------
    # INCOMING MESSAGE
    # -------------------------------------------------
    messages = value.get("messages", [])
    if not messages:
        return JsonResponse({"status": "ok"})

    msg = messages[0]

    msg_id = msg.get("id")
    donor_number = msg.get("from")
    msg_type = msg.get("type")

    if not msg_id or not donor_number or not msg_type:
        return JsonResponse({"status": "ignored"})

    if Message.objects.filter(external_id=msg_id).exists():
        return JsonResponse({"status": "duplicate"})

    with transaction.atomic():

        donor, _ = Donor.objects.get_or_create(phone_number=donor_number)

        conversation = Conversation.objects.select_for_update().filter(
            donor=donor,
            status="open"
        ).first()

        if not conversation:
            rm = RM.objects.filter(is_active=True).order_by("last_assigned_at").first()
            conversation = Conversation.objects.create(donor=donor, rm=rm)
            rm.last_assigned_at = conversation.created_at
            rm.save(update_fields=["last_assigned_at"])

        # ---------------- TEXT ----------------
        if msg_type == "text":
            body = msg.get("text", {}).get("body", "")

            message = Message.objects.create(
                conversation=conversation,
                direction="in",
                body=body,
                message_type="text",
                status="delivered",
                external_id=msg_id
            )

        # ---------------- MEDIA ----------------
        else:
            media_info = msg.get(msg_type, {})
            wa_media_id = media_info.get("id")

            if not wa_media_id:
                return JsonResponse({"status": "ignored"})

            headers = {
                "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}"
            }

            meta_resp = requests.get(
                f"https://graph.facebook.com/v18.0/{wa_media_id}",
                headers=headers,
                timeout=10
            )

            if meta_resp.status_code != 200:
                return JsonResponse({"status": "media_meta_failed"})

            meta = meta_resp.json()

            media_resp = requests.get(
                meta.get("url"),
                headers=headers,
                timeout=20
            )

            if media_resp.status_code != 200:
                return JsonResponse({"status": "media_download_failed"})

            mime = meta.get("mime_type", "")
            ext = mime.split("/")[-1] if "/" in mime else "bin"
            filename = f"{wa_media_id}.{ext}"

            path = default_storage.save(
                f"whatsapp_media/{filename}",
                ContentFile(media_resp.content)
            )

            message = Message.objects.create(
                conversation=conversation,
                direction="in",
                message_type=msg_type,
                status="delivered",
                external_id=msg_id
            )

            MessageMedia.objects.create(
                message=message,
                file=path,
                mime_type=mime,
                size=len(media_resp.content),
                wa_media_id=wa_media_id
            )

    # -------------------------------------------------
    # REALTIME PUSH
    # -------------------------------------------------
    local_time = timezone.localtime(message.created_at)

    ws_payload = {
        "id": message.id,
        "direction": "in",
        "message_type": message.message_type,
        "status": message.status,
        "time": local_time.strftime("%I:%M %p"),
    }

    if message.message_type == "text":
        ws_payload["body"] = message.body
    else:
        ws_payload["file_url"] = message.media.file.url

    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation.id}",
        {
            "type": "chat_message",
            "message": ws_payload
        }
    )

    return JsonResponse({"status": "ok"})
