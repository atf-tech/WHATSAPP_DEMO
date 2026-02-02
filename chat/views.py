from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from whatsapp.services import send_whatsapp_message
from chat.models import Conversation, Message

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Conversation, Message, MessageMedia
from whatsapp.services import upload_media_to_whatsapp, send_whatsapp_media_message


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

    # 1️⃣ Create message (SINGLE TICK)
    message = Message.objects.create(
        conversation=conversation,
        direction="out",
        body=text,
        status="sent",
        message_type="text"
    )

    # update conversation preview
    conversation.last_message_at = message.created_at
    conversation.last_message_preview = text
    conversation.save(update_fields=["last_message_at", "last_message_preview"])

    # 2️⃣ Realtime UI update (DO NOT WAIT FOR WHATSAPP)
    local_time = timezone.localtime(message.created_at)
    channel_layer = get_channel_layer()
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

    # 3️⃣ Send to WhatsApp + save external_id
    try:
        response = send_whatsapp_message(
            to=conversation.donor.phone_number,
            text=text
        )

        wa_id = response["messages"][0]["id"]
        message.external_id = wa_id
        message.save(update_fields=["external_id"])

    except Exception as e:
        # IMPORTANT: never break UI
        print("WhatsApp send failed:", e)

    return HttpResponse(status=204)


@require_POST
@login_required
def send_media_message(request, convo_id):
    rm = request.user.rm

    conversation = get_object_or_404(
        Conversation,
        id=convo_id,
        rm=rm
    )

    uploaded = request.FILES.get("file")
    message_type = request.POST.get("message_type")

    if not uploaded or message_type not in ["image", "video", "audio", "document"]:
        return HttpResponse(status=400)

    # 1️⃣ Create message
    message = Message.objects.create(
        conversation=conversation,
        direction="out",
        message_type=message_type,
        status="sent"
    )

    # 2️⃣ Save media locally
    media = MessageMedia.objects.create(
        message=message,
        file=uploaded,
        mime_type=uploaded.content_type,
        size=uploaded.size
    )

    # 3️⃣ Realtime UI (instant preview)
    channel_layer = get_channel_layer()
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

    # 4️⃣ WhatsApp upload + send
    try:
        wa_media_id = upload_media_to_whatsapp(
            media.file.path,
            media.mime_type
        )

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
        print("Media send failed:", e)

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
