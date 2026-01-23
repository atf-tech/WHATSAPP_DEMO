from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation
from django.views.decorators.http import require_POST
from whatsapp.services import send_whatsapp_message
from .models import Message

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
    rm = request.user.rm

    conversation = get_object_or_404(
        Conversation,
        id=convo_id,
        rm=rm
    )

    messages = conversation.messages.all()

    return render(request, "chat/conversation.html", {
        "conversation": conversation,
        "messages": messages
    })





@require_POST
@login_required
def send_message(request, convo_id):
    rm = request.user.rm
    text = request.POST.get("text")

    conversation = get_object_or_404(
        Conversation,
        id=convo_id,
        rm=rm
    )

    send_whatsapp_message(
        conversation.donor.phone_number,
        text
    )

    Message.objects.create(
        conversation=conversation,
        direction="out",
        body=text
    )

    return redirect("conversation", convo_id=convo_id)



@login_required
def messages_partial(request, convo_id):
    conversation = get_object_or_404(
        Conversation,
        id=convo_id,
        rm=request.user.rm
    )

    messages = conversation.messages.all()

    return render(request, "chat/partials/messages.html", {
        "messages": messages
    })
