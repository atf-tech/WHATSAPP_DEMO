from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Conversation, Message
from whatsapp.services import send_whatsapp_message


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
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from whatsapp.services import send_whatsapp_message
from chat.models import Conversation, Message


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
                "status": message.status,   # sent
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
