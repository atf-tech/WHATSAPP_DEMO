import os
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from chat.utils import convert_webm_to_ogg
from whatsapp.services import send_whatsapp_message
from chat.models import Conversation, Message

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Conversation, Message, MessageMedia, MessageReaction
from whatsapp.services import upload_media_to_whatsapp, send_whatsapp_media_message
from django.core.files import File


@login_required
def inbox(request):
    rm = request.user.rm

    conversations = Conversation.objects.filter(
        rm=rm,
        status="open"
    ).order_by("-last_message_at")

    return render(request, "chat/inbox.html", {
        "conversations": conversations
    })


@login_required
def conversation(request, convo_id):
    conversation = get_object_or_404(
        Conversation,
        id=convo_id,
        rm=request.user.rm
    )

    # 🔥 RESET unread count
    if conversation.unread_count > 0:
        conversation.unread_count = 0
        conversation.save(update_fields=["unread_count"])

        # 🔥 notify inbox in realtime
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"inbox_rm_{request.user.rm.id}",
            {
                "type": "inbox_update",
                "conversation_id": conversation.id,
                "preview": conversation.last_message_preview,
                "unread": 0,
            }
        )


    messages_qs = conversation.messages.all()

    return render(request, "chat/conversation.html", {
        "conversation": conversation,
        "messages": messages_qs
    })

@require_POST
@login_required
def send_message(request, convo_id):
    text = (request.POST.get("text") or "").strip()
    rm = request.user.rm

    if not text:
        return HttpResponse(status=204)

    conversation = get_object_or_404(
        Conversation,
        id=convo_id,
        rm=rm
    )

    # 1️⃣ Save message
    message = Message.objects.create(
        conversation=conversation,
        direction="out",
        body=text,
        status="sent",
        message_type="text"
    )

    conversation.last_message_at = message.created_at
    conversation.last_message_preview = text
    conversation.save(update_fields=["last_message_at", "last_message_preview"])

    local_time = timezone.localtime(message.created_at)
    channel_layer = get_channel_layer()

    # 2️⃣ 🔥 SEND CHAT MESSAGE (THIS WAS MISSING)
    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation.id}",
        {
            "type": "chat_message",
            "message": {
                "id": message.id,
                "body": message.body,
                "direction": "out",
                "message_type": "text",
                "status": message.status,
                "time": local_time.strftime("%I:%M %p"),
            }
        }
    )

    # 3️⃣ 🔥 INBOX UPDATE
    async_to_sync(channel_layer.group_send)(
        f"inbox_rm_{rm.id}",
        {
            "type": "inbox_update",
            "conversation_id": conversation.id,
            "preview": text,
            "unread": conversation.unread_count,
        }
    )

    # 4️⃣ Send to WhatsApp (non-blocking)
    try:
        response = send_whatsapp_message(
            to=conversation.donor.phone_number,
            text=text
        )
        message.external_id = response["messages"][0]["id"]
        message.save(update_fields=["external_id"])
    except Exception as e:
        print("WhatsApp send failed:", e)

    return HttpResponse(status=204)


@require_POST
@login_required
def send_media_message(request, convo_id):
    rm = request.user.rm
    conversation = get_object_or_404(Conversation, id=convo_id, rm=rm)

    uploaded = request.FILES.get("file")
    message_type = request.POST.get("message_type")

    if not uploaded or message_type not in ["image", "video", "audio", "document"]:
        return HttpResponse(status=400)

    # 1️⃣ Save message
    message = Message.objects.create(
        conversation=conversation,
        direction="out",
        message_type=message_type,
        status="sent"
    )

    media = MessageMedia.objects.create(
        message=message,
        file=uploaded,
        mime_type=uploaded.content_type,
        size=uploaded.size
    )

    channel_layer = get_channel_layer()

    # 2️⃣ 🔥 CHAT UPDATE IMMEDIATELY (NO WAIT)
    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation.id}",
        {
            "type": "chat_message",
            "message": {
                "id": message.id,
                "direction": "out",
                "message_type": message_type,
                "file_url": media.file.url,
                "status": message.status,
            }
        }
    )

    # 3️⃣ 🔥 Inbox update immediately
    async_to_sync(channel_layer.group_send)(
        f"inbox_rm_{rm.id}",
        {
            "type": "inbox_update",
            "conversation_id": conversation.id,
            "preview": "🎤 Voice message" if message_type == "audio" else "📎 Media",
            "unread": conversation.unread_count,
        }
    )

    # 4️⃣ ⏳ WhatsApp upload (can be slow — UI already updated)
    try:
        file_path = media.file.path
        mime_type = media.mime_type

        if message_type == "audio" and mime_type == "audio/webm":
            ogg_path = convert_webm_to_ogg(uploaded)
            file_path = ogg_path
            mime_type = "audio/ogg"

        wa_media_id = upload_media_to_whatsapp(file_path, mime_type)

        media.wa_media_id = wa_media_id
        media.save(update_fields=["wa_media_id"])

        res = send_whatsapp_media_message(
            conversation.donor.phone_number,
            wa_media_id,
            message_type
        )

        message.external_id = res["messages"][0]["id"]
        message.save(update_fields=["external_id"])

    except Exception as e:
        print("WhatsApp media send failed:", e)

    return HttpResponse(status=204)



@login_required
def messages_partial(request, convo_id):
    conversation = get_object_or_404(
        Conversation,
        id=convo_id,
        rm=request.user.rm
    )

    messages_qs = conversation.messages.all()

    return render(request, "chat/partials/messages.html", {
        "messages": messages_qs
    })





@require_POST
@login_required
def toggle_reaction(request, message_id):
    rm = request.user.rm
    emoji = request.POST.get("emoji")
    message = get_object_or_404(Message, id=message_id)


    existing = MessageReaction.objects.filter(
        message=message,
        rm=rm
    ).first()

    action = "add"
    
    if existing:
        if existing.emoji == emoji:
            existing.delete()
            action = "remove"
        else:
            existing.emoji = emoji
            existing.save(update_fields=["emoji"])
            action = "update"
    else:
        MessageReaction.objects.create(
            message=message,
            rm=rm,
            emoji=emoji
        )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{message.conversation_id}",
        {
            "type": "reaction_event",
            "message_id": message.id,
            "emoji": emoji,
            "action": action,
        }
    )

    return JsonResponse({"ok": True})
